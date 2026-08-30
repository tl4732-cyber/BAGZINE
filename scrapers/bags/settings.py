import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Load .env from project root (parent of scrapers/)
load_dotenv(ROOT / ".env")

# Scrapy's project name
BOT_NAME = "bags"

# Look for spiders inside bags/spiders/
SPIDER_MODULES = ["bags.spiders"]
NEWSPIDER_MODULE = "bags.spiders"

# It means Scrapy will check a site's robots.txt file and obey the rules.
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
# scrapy will wait 1 second between requests to the same domain.
DOWNLOAD_DELAY = 1

# Pipelines are used to process the data after it is scraped.
# The values themselves are arbitrary integers (Scrapy convention is usually 0–1000); what matters is only their relative order
ITEM_PIPELINES = {
    "bags.pipelines.ValidationPipeline": 100,
    "bags.pipelines.NormalizationPipeline": 200,
    "bags.pipelines.S3RawArchivePipeline": 205,
    "bags.pipelines.JunkListingPipeline": 210,
    "bags.pipelines.ProductLinkPipeline": 250,
    "bags.pipelines.PostgresListingPipeline": 300,
    "bags.pipelines.PriceObservationPipeline": 400,
}


FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
EBAY_ENV = os.getenv("EBAY_ENV", "sandbox")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags",
)

# AWS S3 raw-archive landing zone (bronze layer). Leave S3_ARCHIVE_BUCKET
# unset for local dev — the pipeline no-ops without it. See
# bags/settings_lambda.py for the crawl profile used inside AWS Lambda.
S3_ARCHIVE_BUCKET = os.getenv("S3_ARCHIVE_BUCKET", "")
S3_ARCHIVE_PREFIX = os.getenv("S3_ARCHIVE_PREFIX", "raw")

