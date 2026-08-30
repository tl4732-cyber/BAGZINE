"""Scrapy settings profile used when crawling inside AWS Lambda.

AWS Lambda has no network path back to the local/Docker Postgres instance,
so this profile drops every DB-writing pipeline stage (JunkListingPipeline,
ProductLinkPipeline, PostgresListingPipeline, PriceObservationPipeline) and
keeps only basic validation/normalization plus the S3 raw-archive pipeline.

Load the resulting S3 objects into Postgres from a machine that *can* reach
the database with ``scripts/load_from_s3.py`` — that script replays each
raw item through the full pipeline (junk filtering, product matching,
Postgres upsert), so business logic still lives in one place.
"""

from bags.settings import *  # noqa: F401,F403 -- reuse robots/concurrency/etc.

ITEM_PIPELINES = {
    "bags.pipelines.ValidationPipeline": 100,
    "bags.pipelines.NormalizationPipeline": 200,
    "bags.pipelines.S3RawArchivePipeline": 205,
}

# bags/lambda_handler.py passes spider *classes* directly to
# CrawlerProcess.crawl(), so spider auto-discovery is unnecessary here -- and
# importantly must stay disabled, because Scrapy's SpiderLoader eagerly
# imports every module under SPIDER_MODULES (including
# bags/spiders/therealreal.py, which imports scrapy-playwright). That
# dependency is deliberately not installed in the slim Lambda image
# (requirements-lambda.txt) since only ebay_api/fashionphile run here.
SPIDER_MODULES = []

# /tmp is the only writable filesystem inside a Lambda execution environment.
HTTPCACHE_DIR = "/tmp/httpcache"
TELNETCONSOLE_ENABLED = False
