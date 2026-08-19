"""Unit tests for scripts/spark_silver_consolidate.py (imported via sys.path, not a package).

The full Spark pipeline (``run()``) needs PySpark + a JVM on PATH, which isn't
part of the default dev setup (see requirements-spark.txt) -- those tests are
skipped automatically if pyspark can't be imported, so this file doesn't break
the rest of the suite for anyone who hasn't installed Spark.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "spark_silver_consolidate.py"

_spec = importlib.util.spec_from_file_location("spark_silver_consolidate", MODULE_PATH)
spark_silver_consolidate = importlib.util.module_from_spec(_spec)
sys.modules["spark_silver_consolidate"] = spark_silver_consolidate
_spec.loader.exec_module(spark_silver_consolidate)

try:
    import pyspark  # noqa: F401

    _PYSPARK_AVAILABLE = True
except ImportError:
    _PYSPARK_AVAILABLE = False


class MockDataStagingTest(unittest.TestCase):
    """These don't touch Spark at all -- just the plain-Python staging helpers."""

    def test_mock_records_shape_matches_s3_archive_pipeline_output(self):
        runs = spark_silver_consolidate._mock_records()
        self.assertEqual(len(runs), 2)
        for run in runs:
            for record in run:
                for field in ("marketplace", "source_listing_id", "url", "price_amount", "scraped_at"):
                    self.assertIn(field, record)

    def test_stage_mock_writes_one_jsonl_file_per_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging_dir = Path(tmp)
            spark_silver_consolidate._stage_mock(staging_dir)
            files = sorted(staging_dir.glob("*.jsonl"))
            self.assertEqual(len(files), 2)
            lines = [json.loads(line) for line in files[0].read_text().splitlines() if line.strip()]
            self.assertEqual(len(lines), 3)


@unittest.skipUnless(_PYSPARK_AVAILABLE, "pyspark not installed -- see requirements-spark.txt")
class SilverConsolidateSparkTest(unittest.TestCase):
    """End-to-end: mock bronze data in, deduped Parquet out. Needs a JVM on PATH."""

    def test_dedupes_across_runs_and_keeps_latest_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging_dir = Path(tmp) / "staging"
            output_dir = Path(tmp) / "silver"
            staging_dir.mkdir()
            spark_silver_consolidate._stage_mock(staging_dir)

            stats = spark_silver_consolidate.run(staging_dir, output_dir)

            # 3 listings x 2 runs = 6 raw rows staged.
            self.assertEqual(stats["raw_rows"], 6)
            # 3 distinct listings (ebay-A, ebay-B, fp-C).
            self.assertEqual(stats["distinct_listings"], 3)
            # ebay-A has 2 distinct prices, ebay-B's repeat is deduped to 1,
            # fp-C is unchanged -> 1. Total = 4.
            self.assertEqual(stats["distinct_price_states"], 4)
            self.assertTrue((output_dir / "listings_latest" / "_SUCCESS").exists())
            self.assertTrue((output_dir / "price_history" / "_SUCCESS").exists())

    def test_backfills_missing_condition_normalized_from_older_bronze_objects(self):
        """fp-C's first mock record has no condition_normalized/content_hash at all,
        simulating an object archived before a pipeline change. The job should
        recompute it defensively rather than dropping/erroring on the row."""
        with tempfile.TemporaryDirectory() as tmp:
            staging_dir = Path(tmp) / "staging"
            output_dir = Path(tmp) / "silver"
            staging_dir.mkdir()
            spark_silver_consolidate._stage_mock(staging_dir)

            spark_silver_consolidate.run(staging_dir, output_dir)

            from pyspark.sql import SparkSession

            spark = SparkSession.builder.master("local[1]").getOrCreate()
            try:
                latest = spark.read.parquet(str(output_dir / "listings_latest"))
                row = latest.filter(latest.source_listing_id == "fp-C").collect()[0]
                self.assertEqual(row["condition_normalized"], "excellent")
            finally:
                spark.stop()


if __name__ == "__main__":
    unittest.main()
