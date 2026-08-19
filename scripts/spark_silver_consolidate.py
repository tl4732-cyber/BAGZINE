#!/usr/bin/env python3
"""Batch-consolidate the S3 bronze archive into a deduplicated "silver" layer using PySpark.

This complements, not replaces, scripts/load_from_s3.py. That script does
row-by-row product-matching + Postgres upserts (it needs a live DB
connection). This job is read-only and DB-free: it uses Spark DataFrames to
recompute normalized, deduplicated views of the *entire* raw archive as
columnar Parquet, independent of Postgres. Useful for:

  - Historical/at-scale analysis over every crawl run ever archived, without
    touching the production database.
  - Reprocessing after a normalization/logic change without needing to
    replay everything through Postgres.
  - Collapsing N daily crawl files (which re-scrape unchanged listings every
    day) down to only the *distinct* states a listing has ever had, which is
    the same "keep only what changed" idea as PostgresListingPipeline /
    PriceObservationPipeline, just recomputed independently in a columnar
    batch job instead of row-by-row against a live database.

Two output datasets (Parquet, partitioned by marketplace):
  - listings_latest/  -- one row per (marketplace, source_listing_id): the
    most recently observed state of that listing.
  - price_history/    -- one row per distinct (marketplace,
    source_listing_id, silver_content_hash): every unique state a listing
    has been observed in, i.e. a batch-recomputed price/condition history.

Design notes:
  - Runs entirely in Spark "local mode" (master=local[*]) -- no cluster, no
    AWS Glue/EMR, no compute cost. boto3 stages new bronze objects to a
    local temp dir first; Spark itself never talks to S3 directly. This
    sidesteps the notoriously fiddly hadoop-aws/aws-java-sdk classpath setup
    that a bare `pip install pyspark` doesn't include.
  - `silver_content_hash` is deliberately a *new* column, not a rewrite of
    the `content_hash` that scrapers/bags/utils.py computed at scrape time.
    It's recomputed defensively here (falling back to `normalize_condition`
    when `condition_normalized` is missing) so this job stays correct even
    against older bronze objects written before a pipeline change -- but
    that means it is not guaranteed to be byte-identical to the original,
    since Spark's JSON schema inference doesn't always preserve `attributes_raw`
    exactly as the original dict was shaped.
  - Requires a JVM (Java 17+) on PATH -- PySpark is a Python API over the
    JVM Spark engine. See requirements-spark.txt / README for setup.

Usage:
    python3 scripts/spark_silver_consolidate.py --use-mock                  # offline demo, no AWS
    python3 scripts/spark_silver_consolidate.py                             # reads S3_ARCHIVE_BUCKET
    python3 scripts/spark_silver_consolidate.py --bucket my-bucket --since-days 30
    python3 scripts/spark_silver_consolidate.py --local-dir data/bronze_staging --keep-staging
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scrapers"))
sys.path.insert(0, str(ROOT))

# PySpark's UDFs run in separate worker subprocesses (even in local mode) that
# don't inherit the driver's sys.path -- only PYTHONPATH from the environment.
# Must be set before the SparkSession/workers are created.
os.environ["PYTHONPATH"] = os.pathsep.join(
    [str(ROOT / "scrapers"), str(ROOT), os.environ.get("PYTHONPATH", "")]
)

from bags.utils import compute_content_hash, normalize_condition  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("spark_silver_consolidate")

DEFAULT_OUTPUT_DIR = ROOT / "data" / "silver"


def _mock_records() -> list[list[dict]]:
    """Two mock "crawl run" files shaped like real S3RawArchivePipeline output.

    Deliberately includes: a listing whose price changes between runs (A), a
    listing scraped twice with an unchanged price (B, to prove dedup collapses
    it to one price_history row), and a listing missing condition_normalized/
    content_hash entirely (C, run 1) to simulate an older bronze object
    written before a pipeline change -- exercising the defensive
    re-normalization path.
    """
    run1 = [
        {
            "marketplace": "ebay",
            "source_listing_id": "ebay-A",
            "url": "https://example.com/ebay-A",
            "title": "Chanel Classic Flap Medium Black Caviar",
            "price_amount": 1200.0,
            "currency": "USD",
            "condition_raw": "Pre-owned - Very Good",
            "condition_normalized": "very_good",
            "attributes_raw": {"size": "Medium"},
            "status": "active",
            "scraped_at": "2026-08-12T09:00:00+00:00",
        },
        {
            "marketplace": "ebay",
            "source_listing_id": "ebay-B",
            "url": "https://example.com/ebay-B",
            "title": "Louis Vuitton Neverfull MM Damier Ebene",
            "price_amount": 800.0,
            "currency": "USD",
            "condition_raw": "Good",
            "condition_normalized": "good",
            "attributes_raw": {"size": "MM"},
            "status": "active",
            "scraped_at": "2026-08-12T09:00:05+00:00",
        },
        {
            # Simulates a bronze object from before condition/hash were computed.
            "marketplace": "fashionphile",
            "source_listing_id": "fp-C",
            "url": "https://example.com/fp-C",
            "title": "Hermes Birkin 30 Togo Gold Hardware",
            "price_amount": 22000.0,
            "currency": "USD",
            "condition_raw": "Excellent",
            "attributes_raw": {"size": "30"},
            "status": "active",
            "scraped_at": "2026-08-12T09:00:10+00:00",
        },
    ]
    run2 = [
        {
            "marketplace": "ebay",
            "source_listing_id": "ebay-A",
            "url": "https://example.com/ebay-A",
            "title": "Chanel Classic Flap Medium Black Caviar",
            "price_amount": 1150.0,  # price dropped -> new distinct state
            "currency": "USD",
            "condition_raw": "Pre-owned - Very Good",
            "condition_normalized": "very_good",
            "attributes_raw": {"size": "Medium"},
            "status": "active",
            "scraped_at": "2026-08-13T09:00:00+00:00",
        },
        {
            "marketplace": "ebay",
            "source_listing_id": "ebay-B",
            "url": "https://example.com/ebay-B",
            "title": "Louis Vuitton Neverfull MM Damier Ebene",
            "price_amount": 800.0,  # unchanged -> should dedup with run1's row
            "currency": "USD",
            "condition_raw": "Good",
            "condition_normalized": "good",
            "attributes_raw": {"size": "MM"},
            "status": "active",
            "scraped_at": "2026-08-13T09:00:05+00:00",
        },
        {
            "marketplace": "fashionphile",
            "source_listing_id": "fp-C",
            "url": "https://example.com/fp-C",
            "title": "Hermes Birkin 30 Togo Gold Hardware",
            "price_amount": 22000.0,
            "currency": "USD",
            "condition_raw": "Excellent",
            "condition_normalized": "excellent",
            "attributes_raw": {"size": "30"},
            "status": "active",
            "scraped_at": "2026-08-13T09:00:10+00:00",
        },
    ]
    return [run1, run2]


def _stage_mock(staging_dir: Path) -> None:
    for i, run in enumerate(_mock_records(), start=1):
        path = staging_dir / f"mock_run_{i}.jsonl"
        path.write_text("\n".join(json.dumps(rec) for rec in run))
    logger.info("Staged %d mock crawl-run file(s) into %s", len(_mock_records()), staging_dir)


def _stage_from_s3(bucket: str, prefix: str, since_days: int | None, staging_dir: Path) -> int:
    import boto3

    s3 = boto3.client("s3")
    since = datetime.now(timezone.utc) - timedelta(days=since_days) if since_days else None

    count = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if since and obj["LastModified"] < since:
                continue
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            local_path = staging_dir / f"{count}_{uuid.uuid4().hex[:8]}.jsonl"
            local_path.write_bytes(body)
            count += 1
    logger.info("Staged %d object(s) from s3://%s/%s", count, bucket, prefix)
    return count


def _build_spark():
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("bagzine-silver-consolidate")
        .config("spark.sql.shuffle.partitions", "4")  # small local dataset; default 200 is overkill
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def run(staging_dir: Path, output_dir: Path) -> dict:
    from pyspark.sql import functions as F
    from pyspark.sql import types as T
    from pyspark.sql.window import Window

    spark = _build_spark()
    try:
        df = spark.read.json(str(staging_dir))
        raw_count = df.count()
        if raw_count == 0:
            logger.warning("No records found under %s -- nothing to do", staging_dir)
            return {"raw_rows": 0}

        condition_udf = F.udf(normalize_condition, T.StringType())

        def _hash_row(title, price_amount, currency, condition_normalized, status, attributes_raw_json):
            return compute_content_hash(
                {
                    "title": title,
                    "price_amount": price_amount,
                    "currency": currency,
                    "condition_normalized": condition_normalized,
                    "status": status,
                    "attributes_raw": attributes_raw_json,
                }
            )

        hash_udf = F.udf(_hash_row, T.StringType())

        normalized = df.withColumn(
            "condition_normalized",
            F.coalesce(F.col("condition_normalized"), condition_udf(F.col("condition_raw"))),
        ).withColumn("status", F.coalesce(F.col("status"), F.lit("active")))

        normalized = normalized.withColumn(
            "silver_content_hash",
            hash_udf(
                F.col("title"),
                F.col("price_amount"),
                F.col("currency"),
                F.col("condition_normalized"),
                F.col("status"),
                F.to_json(F.col("attributes_raw")),
            ),
        ).withColumn("scraped_at_ts", F.to_timestamp(F.col("scraped_at")))

        window = Window.partitionBy("marketplace", "source_listing_id").orderBy(
            F.col("scraped_at_ts").desc()
        )
        latest = (
            normalized.withColumn("_rn", F.row_number().over(window))
            .filter(F.col("_rn") == 1)
            .drop("_rn")
        )
        history = normalized.dropDuplicates(["marketplace", "source_listing_id", "silver_content_hash"])

        output_dir.mkdir(parents=True, exist_ok=True)
        latest.write.mode("overwrite").partitionBy("marketplace").parquet(
            str(output_dir / "listings_latest")
        )
        history.write.mode("overwrite").partitionBy("marketplace").parquet(
            str(output_dir / "price_history")
        )

        summary = (
            history.groupBy("marketplace", "condition_normalized")
            .agg(
                F.count("*").alias("distinct_states"),
                F.round(F.avg("price_amount"), 2).alias("avg_price"),
                F.round(F.min("price_amount"), 2).alias("min_price"),
                F.round(F.max("price_amount"), 2).alias("max_price"),
            )
            .orderBy("marketplace", "condition_normalized")
        )
        summary.show(truncate=False)

        stats = {
            "raw_rows": raw_count,
            "distinct_listings": latest.count(),
            "distinct_price_states": history.count(),
        }
        return stats
    finally:
        spark.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--use-mock", action="store_true", help="Use built-in mock data, no AWS needed")
    parser.add_argument("--bucket", default=None, help="Override S3_ARCHIVE_BUCKET env var")
    parser.add_argument("--prefix", default=None, help="Override S3_ARCHIVE_PREFIX env var")
    parser.add_argument("--since-days", type=int, default=None, help="Only consider objects from the last N days")
    parser.add_argument("--local-dir", default=None, help="Read already-downloaded .jsonl files from this directory instead of S3")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for silver Parquet")
    parser.add_argument("--keep-staging", action="store_true", help="Don't delete the local staging directory afterwards")
    args = parser.parse_args()

    output_dir = Path(args.output)
    owns_staging = args.local_dir is None
    staging_dir = Path(args.local_dir) if args.local_dir else Path(tempfile.mkdtemp(prefix="bagzine_bronze_"))
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.local_dir:
            logger.info("Reading pre-staged bronze files from %s", staging_dir)
        elif args.use_mock:
            _stage_mock(staging_dir)
        else:
            import os

            bucket = args.bucket or os.environ.get("S3_ARCHIVE_BUCKET")
            prefix = args.prefix or os.environ.get("S3_ARCHIVE_PREFIX", "raw")
            if not bucket:
                logger.error("S3_ARCHIVE_BUCKET is not set (env var or --bucket) -- or pass --use-mock / --local-dir")
                return 1
            n = _stage_from_s3(bucket, prefix, args.since_days, staging_dir)
            if n == 0:
                logger.info("Nothing new to process")
                return 0

        stats = run(staging_dir, output_dir)
        logger.info("Done: %s", json.dumps(stats))
        logger.info("Silver Parquet written to %s", output_dir)
        return 0
    finally:
        if owns_staging and not args.keep_staging:
            shutil.rmtree(staging_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
