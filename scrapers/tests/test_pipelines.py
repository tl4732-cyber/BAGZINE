import unittest

from scrapy.exceptions import DropItem

from bags.items import ListingItem
from bags.pipelines import JunkListingPipeline, NormalizationPipeline, ValidationPipeline
from bags.utils import normalize_condition


class _FakeSpider:
    name = "test"
    logger = type("L", (), {"warning": lambda *a, **k: None})()


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.spider = _FakeSpider()
        self.validation = ValidationPipeline()
        self.normalization = NormalizationPipeline()
        self.junk = JunkListingPipeline()

    def _valid_item(self):
        item = ListingItem()
        item["marketplace"] = "ebay"
        item["source_listing_id"] = "abc-123"
        item["url"] = "https://www.ebay.com/itm/abc-123"
        item["title"] = "  Chanel Bag  "
        item["price_amount"] = 2500.0
        item["currency"] = "usd"
        item["condition_raw"] = "Pre-owned"
        return item

    def test_validation_accepts_good_item(self):
        result = self.validation.process_item(self._valid_item(), self.spider)
        self.assertEqual(result["marketplace"], "ebay")

    def test_validation_drops_bad_price(self):
        item = self._valid_item()
        item["price_amount"] = 0
        with self.assertRaises(DropItem):
            self.validation.process_item(item, self.spider)

    def test_normalization_enriches_item(self):
        item = self.validation.process_item(self._valid_item(), self.spider)
        result = self.normalization.process_item(item, self.spider)
        self.assertEqual(result["title"], "Chanel Bag")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["condition_normalized"], "unknown")
        self.assertEqual(result["status"], "active")
        self.assertTrue(result["content_hash"])
        self.assertTrue(result["scraped_at"])

    def test_condition_normalization_uses_fixed_scale(self):
        self.assertEqual(normalize_condition("Pre-Owned - Excellent"), "excellent")
        self.assertEqual(normalize_condition("Pre-Owned - Good"), "good")
        self.assertEqual(normalize_condition("Used"), "unknown")
        self.assertEqual(normalize_condition(None), "unknown")

    def test_condition_normalization_handles_fashionphile_vocabulary(self):
        self.assertEqual(normalize_condition("Excellent"), "excellent")
        self.assertEqual(normalize_condition("Shows Wear"), "good")
        self.assertEqual(normalize_condition("Worn"), "fair")
        self.assertEqual(normalize_condition("Flawed"), "poor")
        self.assertEqual(normalize_condition("Giftable"), "new")

    def test_junk_pipeline_keeps_low_priced_real_bag_for_anomaly_review(self):
        item = self._valid_item()
        item["title"] = "Hermes Birkin 30 Togo Gold"
        item["price_amount"] = 7500.0
        result = self.junk.process_item(item, self.spider)
        self.assertEqual(result["title"], "Hermes Birkin 30 Togo Gold")


if __name__ == "__main__":
    unittest.main()
