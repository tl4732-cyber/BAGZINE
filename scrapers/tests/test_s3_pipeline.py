import json
import unittest

import boto3
from moto import mock_aws

from bags.items import ListingItem
from bags.pipelines import S3RawArchivePipeline


class _FakeSpider:
    name = "ebay_api"
    logger = type("L", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})()


class _FakeCrawler:
    def __init__(self, settings: dict):
        self.settings = settings


def _item(source_id: str) -> ListingItem:
    item = ListingItem()
    item["marketplace"] = "ebay"
    item["source_listing_id"] = source_id
    item["url"] = f"https://www.ebay.com/itm/{source_id}"
    item["title"] = "Chanel Classic Flap Medium Caviar Black"
    item["price_amount"] = 6200.0
    item["currency"] = "USD"
    return item


class S3RawArchivePipelineTest(unittest.TestCase):
    def test_noop_without_bucket_configured(self):
        pipeline = S3RawArchivePipeline.from_crawler(_FakeCrawler({}))
        spider = _FakeSpider()
        pipeline.open_spider(spider)
        result = pipeline.process_item(_item("1"), spider)
        pipeline.close_spider(spider)  # should not raise / not touch AWS
        self.assertEqual(result["source_listing_id"], "1")

    @mock_aws
    def test_archives_buffered_items_as_one_object_per_run(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="bagzine-test-bucket")

        pipeline = S3RawArchivePipeline.from_crawler(
            _FakeCrawler({"S3_ARCHIVE_BUCKET": "bagzine-test-bucket", "S3_ARCHIVE_PREFIX": "raw"})
        )
        spider = _FakeSpider()
        pipeline.open_spider(spider)
        pipeline.process_item(_item("1"), spider)
        pipeline.process_item(_item("2"), spider)
        pipeline.close_spider(spider)

        objects = s3.list_objects_v2(Bucket="bagzine-test-bucket", Prefix="raw/ebay_api/")
        keys = [obj["Key"] for obj in objects.get("Contents", [])]
        self.assertEqual(len(keys), 1, "expected exactly one archive object per spider run")

        body = s3.get_object(Bucket="bagzine-test-bucket", Key=keys[0])["Body"].read().decode("utf-8")
        lines = [json.loads(line) for line in body.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual({row["source_listing_id"] for row in lines}, {"1", "2"})

    @mock_aws
    def test_no_object_written_when_no_items_scraped(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="bagzine-test-bucket")

        pipeline = S3RawArchivePipeline.from_crawler(
            _FakeCrawler({"S3_ARCHIVE_BUCKET": "bagzine-test-bucket", "S3_ARCHIVE_PREFIX": "raw"})
        )
        spider = _FakeSpider()
        pipeline.open_spider(spider)
        pipeline.close_spider(spider)

        objects = s3.list_objects_v2(Bucket="bagzine-test-bucket")
        self.assertNotIn("Contents", objects)


if __name__ == "__main__":
    unittest.main()
