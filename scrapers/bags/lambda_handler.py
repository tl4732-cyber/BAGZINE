"""AWS Lambda entrypoint: run scheduled Scrapy crawls and archive raw items to S3.

Deployed as a container image (see ``Dockerfile.lambda``) and invoked on a
cron schedule by EventBridge (see ``infra/terraform``). Only spiders with no
browser dependency and no network path back to Postgres are run here
(``ebay_api``, ``fashionphile``) — see ``bags/settings_lambda.py`` for the
DB-free pipeline profile used for the crawl. Loading the archived S3 objects
into Postgres happens separately via ``scripts/load_from_s3.py``, run from a
machine that can reach the database.

Handler: ``bags.lambda_handler.handler``
"""

from __future__ import annotations

import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mirrors scripts/crawl_daily.sh so the Lambda schedule and the local manual
# crawl cover the same flagship models. Keep the two lists in sync when a new
# brand/model is added to title_parser.py.
DEFAULT_JOBS: list[dict] = [
    {
        "spider": "ebay_api",
        "query": "Hermes Birkin leather handbag -vinyl -PVC -organizer -dust -candle -poster -silicone",
        "limit": 100,
        "paginate": True,
    },
    {
        "spider": "ebay_api",
        "query": "Hermes Kelly leather handbag Sellier Retourne -vinyl -PVC -organizer -cut -wallet -watch -quartz",
        "limit": 100,
        "paginate": True,
    },
    {"spider": "ebay_api", "query": "Hermes Constance bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Chanel classic flap bag -organizer", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Chanel Boy bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {
        "spider": "ebay_api",
        "query": "Louis Vuitton Neverfull bag -wallet -organizer -charm",
        "limit": 100,
        "paginate": True,
    },
    {"spider": "ebay_api", "query": "Louis Vuitton Speedy bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {
        "spider": "ebay_api",
        "query": "Louis Vuitton Pochette Metis bag -wallet -organizer -charm",
        "limit": 100,
        "paginate": True,
    },
    {"spider": "ebay_api", "query": "Gucci Marmont bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Fendi Baguette bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Celine Luggage bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {
        "spider": "ebay_api",
        "query": "Christian Dior Lady Dior bag -wallet -organizer -charm",
        "limit": 100,
        "paginate": True,
    },
    {"spider": "ebay_api", "query": "Christian Dior Saddle bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Prada Galleria bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "ebay_api", "query": "Saint Laurent Loulou bag -wallet -organizer -charm", "limit": 100, "paginate": True},
    {"spider": "fashionphile", "max_pages": 3},
]


def _build_settings():
    from scrapy.settings import Settings

    from bags import settings_lambda as settings_module

    settings = Settings()
    settings.setmodule(settings_module, priority="project")
    return settings


def handler(event, context):  # noqa: ARG001 -- `context` required by Lambda contract
    """Run the configured crawl jobs once and archive results to S3.

    ``event`` may optionally carry ``{"jobs": [...]}`` to override
    ``DEFAULT_JOBS`` for a one-off/ad hoc invocation (e.g. from the AWS
    console "Test" button), using the same shape as ``DEFAULT_JOBS`` entries.
    """
    from scrapy.crawler import CrawlerProcess

    from bags.spiders.ebay_api import EbayApiSpider
    from bags.spiders.fashionphile import FashionphileSpider

    bucket = os.environ.get("S3_ARCHIVE_BUCKET")
    if not bucket:
        logger.warning(
            "S3_ARCHIVE_BUCKET is not set - crawled items will be dropped after this run"
        )

    jobs = (event or {}).get("jobs") or DEFAULT_JOBS
    spider_classes = {"ebay_api": EbayApiSpider, "fashionphile": FashionphileSpider}

    process = CrawlerProcess(_build_settings())
    started = 0
    for job in jobs:
        spider_cls = spider_classes.get(job.get("spider"))
        if spider_cls is None:
            logger.warning("Unknown spider %r, skipping job", job.get("spider"))
            continue
        kwargs = {k: v for k, v in job.items() if k != "spider"}
        process.crawl(spider_cls, **kwargs)
        started += 1

    process.start()  # blocks until every crawl in this batch finishes

    result = {
        "jobs_started": started,
        "jobs_total": len(jobs),
        "bucket": bucket,
        "prefix": os.environ.get("S3_ARCHIVE_PREFIX", "raw"),
    }
    logger.info("Lambda crawl run complete: %s", json.dumps(result))
    return result
