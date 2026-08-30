"""Unit tests for scripts/load_from_s3.py (imported via sys.path, not a package)."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "load_from_s3.py"

_spec = importlib.util.spec_from_file_location("load_from_s3", MODULE_PATH)
load_from_s3 = importlib.util.module_from_spec(_spec)
sys.modules["load_from_s3"] = load_from_s3
_spec.loader.exec_module(load_from_s3)


class LoadFromS3StateTest(unittest.TestCase):
    def test_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "s3_loaded_keys.json"
            load_from_s3.STATE_FILE = state_file

            self.assertEqual(load_from_s3._load_state(), set())
            load_from_s3._save_state({"raw/ebay_api/2026/08/01/a.jsonl"})
            self.assertEqual(
                load_from_s3._load_state(), {"raw/ebay_api/2026/08/01/a.jsonl"}
            )


class RunStagesTest(unittest.TestCase):
    def test_junk_item_is_dropped_before_touching_the_database(self):
        spider = load_from_s3._DummySpider()
        junk_stage = load_from_s3.JunkListingPipeline()
        record = {
            "marketplace": "ebay",
            "source_listing_id": "999",
            "url": "https://www.ebay.com/itm/999",
            "title": "Zoomoni Bag Organizer for Hermes Kelly 32",
            "price_amount": 45.0,
            "currency": "USD",
        }
        loaded = load_from_s3._run_stages(record, [junk_stage], spider)
        self.assertFalse(loaded)


if __name__ == "__main__":
    unittest.main()
