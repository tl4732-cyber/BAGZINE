#!/usr/bin/env python3
"""Load raw listings archived to S3 (by the Lambda scraper) into Postgres.

Replays each S3-archived item through the same junk-filtering, product-
matching, and upsert pipeline stages the local Scrapy crawl uses
(scrapers/bags/pipelines.py), so business logic lives in exactly one place
whether a listing was scraped locally or by the AWS Lambda crawler.

Usage:
    python3 scripts/load_from_s3.py                 # process every new object
    python3 scripts/load_from_s3.py --dry-run        # list what would load
    python3 scripts/load_from_s3.py --since-days 7   # ignore older archives
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scrapers"))
sys.path.insert(0, str(ROOT))

import boto3  # noqa: E402
from scrapy.exceptions import DropItem  # noqa: E402

from bags.pipelines import (  # noqa: E402
    JunkListingPipeline,
    PostgresListingPipeline,
    PriceObservationPipeline,
    ProductLinkPipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("load_from_s3")

STATE_FILE = ROOT / "logs" / "s3_loaded_keys.json"


class _DummySpider:
    """Minimal stand-in so pipeline stages can call spider.logger.*."""

    name = "s3_loader"
    logger = logger


def _load_state() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    return set(json.loads(STATE_FILE.read_text()))


def _save_state(keys: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(keys)))


def _list_new_keys(s3, bucket: str, prefix: str, since: datetime | None, seen: set[str]):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"] in seen:
                continue
            if since and obj["LastModified"] < since:
                continue
            yield obj["Key"]


def _run_stages(item: dict, stages: list, spider) -> bool:
    """Run one raw item through the pipeline stages. Returns False if dropped."""
    for stage in stages:
        try:
            item = stage.process_item(item, spider)
        except DropItem as exc:
            logger.info("Dropped: %s", exc)
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="List new objects without loading them")
    parser.add_argument(
        "--since-days", type=int, default=None, help="Only consider objects modified in the last N days"
    )
    parser.add_argument("--bucket", default=None, help="Override S3_ARCHIVE_BUCKET env var")
    parser.add_argument("--prefix", default=None, help="Override S3_ARCHIVE_PREFIX env var")
    args = parser.parse_args()

    bucket = args.bucket or os.environ.get("S3_ARCHIVE_BUCKET")
    prefix = args.prefix or os.environ.get("S3_ARCHIVE_PREFIX", "raw")
    if not bucket:
        logger.error("S3_ARCHIVE_BUCKET is not set (env var or --bucket)")
        return 1

    since = None
    if args.since_days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    s3 = boto3.client("s3")
    processed_keys = _load_state()
    new_keys = list(_list_new_keys(s3, bucket, prefix, since, processed_keys))

    if not new_keys:
        logger.info("No new objects under s3://%s/%s", bucket, prefix)
        return 0

    logger.info("Found %d new object(s) under s3://%s/%s", len(new_keys), bucket, prefix)
    if args.dry_run:
        for key in new_keys:
            print(key)
        return 0

    spider = _DummySpider()
    postgres = PostgresListingPipeline()
    postgres.open_spider(spider)
    stages = [JunkListingPipeline(), ProductLinkPipeline(), postgres, PriceObservationPipeline()]

    loaded = 0
    dropped = 0
    try:
        for key in new_keys:
            body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if _run_stages(record, stages, spider):
                    loaded += 1
                else:
                    dropped += 1
            processed_keys.add(key)
    finally:
        postgres.close_spider(spider)
        _save_state(processed_keys)

    logger.info("Loaded %d listing(s), dropped %d as junk/unmatched", loaded, dropped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
