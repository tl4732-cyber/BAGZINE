"""
Fashionphile handbag listings spider.

Fashionphile runs on Shopify and exposes the standard, public, unauthenticated
storefront JSON API (`/collections/<handle>/products.json`). Unlike The RealReal
(PerimeterX behavioral CAPTCHA on every request) or Poshmark (robots.txt disallows
/listings and /search), Fashionphile serves plain server-rendered HTML and JSON
with no bot challenge, and robots.txt allows crawling /collections and /products.
No browser automation is required.

Two-stage crawl:
  1. Page through the "handbags" collection JSON feed to discover product handles
     and cheaply filter to brands we track (via the `vendor` field).
  2. Fetch each matching product page (plain HTML) for the condition rating and
     JSON-LD structured data (name, brand, price, currency), which the Shopify
     collection feed does not include.

Offline test (no network):
  scrapy crawl fashionphile -a use_mock=1 -o out.json

Live scrape:
  scrapy crawl fashionphile -o out.json
"""

import json
import re

import scrapy

from bags.items import ListingItem
from bags.title_parser import _find_brand, _normalize_text

COLLECTION_HANDLE = "handbags"
PAGE_SIZE = 250
MAX_PAGES = 40  # safety cap; ~250 items/page covers the catalog comfortably

CONDITION_RE = re.compile(r'condition is\s*"([^"]+)"', re.IGNORECASE)


class FashionphileSpider(scrapy.Spider):
    name = "fashionphile"
    allowed_domains = ["fashionphile.com", "www.fashionphile.com"]

    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        },
    }

    def __init__(self, use_mock=None, max_pages=MAX_PAGES, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_mock = use_mock in (True, "true", "1", 1)
        self.max_pages = int(max_pages)

    def log_error(self, failure):
        self.logger.error(repr(failure))

    def _collection_url(self, page: int) -> str:
        return (
            f"https://www.fashionphile.com/collections/{COLLECTION_HANDLE}/products.json"
            f"?limit={PAGE_SIZE}&page={page}"
        )

    def _is_tracked_brand(self, vendor: str | None) -> bool:
        if not vendor:
            return False
        return _find_brand(_normalize_text(vendor)) is not None

    async def start(self):
        if self.use_mock:
            self.logger.info("use_mock=1 — yielding sample Fashionphile items (no network)")
            for item in self._mock_items():
                yield item
            return

        yield scrapy.Request(
            self._collection_url(1),
            callback=self.parse_collection,
            errback=self.log_error,
            meta={"page": 1},
        )

    def parse_collection(self, response):
        page = response.meta["page"]
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Non-JSON response from collection feed on page %s", page)
            return

        products = data.get("products") or []
        self.logger.info("Collection page %s: %d products", page, len(products))

        matched = 0
        for product in products:
            vendor = product.get("vendor")
            if not self._is_tracked_brand(vendor):
                continue
            handle = product.get("handle")
            if not handle:
                continue
            matched += 1
            yield scrapy.Request(
                f"https://www.fashionphile.com/products/{handle}",
                callback=self.parse_product,
                errback=self.log_error,
                meta={"vendor": vendor},
            )

        self.logger.info("Collection page %s: %d matched tracked brands", page, matched)

        if products and page < self.max_pages:
            yield scrapy.Request(
                self._collection_url(page + 1),
                callback=self.parse_collection,
                errback=self.log_error,
                meta={"page": page + 1},
            )

    def parse_product(self, response):
        product_data = self._extract_json_ld(response)
        if not product_data:
            self.logger.warning("No Product JSON-LD found: %s", response.url)
            return

        offers = product_data.get("offers")
        offer = offers[0] if isinstance(offers, list) and offers else (offers or {})

        title = product_data.get("name")
        price = offer.get("price")
        currency = offer.get("priceCurrency", "USD")
        sku = product_data.get("sku") or response.url.rstrip("/").split("/")[-1]
        brand = (product_data.get("brand") or {}).get("name") or response.meta.get("vendor")

        if not title or price is None:
            self.logger.warning("Missing title/price, skipping: %s", response.url)
            return

        condition = self._extract_condition(response)

        item = ListingItem()
        item["marketplace"] = "fashionphile"
        item["source_listing_id"] = str(sku)
        item["url"] = product_data.get("url") or response.url
        item["title"] = title
        item["price_amount"] = float(price)
        item["currency"] = currency
        item["condition_raw"] = condition
        item["attributes_raw"] = {"brand": brand} if brand else {}
        yield item

    def _extract_json_ld(self, response) -> dict | None:
        for raw in response.css("script[type='application/ld+json']::text").getall():
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                return data
        return None

    def _extract_condition(self, response) -> str | None:
        description = response.css("#fp-condition-description::text").get()
        if description:
            match = CONDITION_RE.search(description)
            if match:
                return match.group(1).strip()
        return response.css(
            ".fp-product__condition-accordion .fp-font-weight--regular::text"
        ).get()

    def _mock_items(self):
        mocks = [
            {
                "sku": "mock-fp-1",
                "url": "https://www.fashionphile.com/products/mock-hermes-birkin-30-togo-gold",
                "title": "Hermes Togo Birkin 30 Gold",
                "price": 18200.0,
                "currency": "USD",
                "brand": "Hermes",
                "condition": "Excellent",
            },
            {
                "sku": "mock-fp-2",
                "url": "https://www.fashionphile.com/products/mock-chanel-classic-double-flap",
                "title": "Chanel Caviar Classic Double Flap Medium Black",
                "price": 6850.0,
                "currency": "USD",
                "brand": "Chanel",
                "condition": "Very Good",
            },
        ]
        for row in mocks:
            item = ListingItem()
            item["marketplace"] = "fashionphile"
            item["source_listing_id"] = row["sku"]
            item["url"] = row["url"]
            item["title"] = row["title"]
            item["price_amount"] = row["price"]
            item["currency"] = row["currency"]
            item["condition_raw"] = row["condition"]
            item["attributes_raw"] = {"brand": row["brand"]}
            yield item
