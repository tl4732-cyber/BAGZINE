import json
import unittest

from scrapy import Request
from scrapy.http import HtmlResponse, TextResponse

from bags.items import ListingItem
from bags.spiders.fashionphile import FashionphileSpider


def _collection_response(products: list[dict], page: int = 1) -> TextResponse:
    url = f"https://www.fashionphile.com/collections/handbags/products.json?limit=250&page={page}"
    request = Request(url, meta={"page": page})
    return TextResponse(
        url=url,
        body=json.dumps({"products": products}).encode(),
        encoding="utf-8",
        request=request,
    )


def _product_response(url: str, html: str, *, vendor: str) -> HtmlResponse:
    request = Request(url, meta={"vendor": vendor})
    return HtmlResponse(url=url, body=html.encode(), encoding="utf-8", request=request)


def _product_html(json_ld: dict, condition_description: str | None) -> str:
    condition_block = ""
    if condition_description:
        condition_block = (
            f'<p id="fp-condition-description">{condition_description}</p>'
        )
    return f"""
    <html><body>
      {condition_block}
      <script type="application/ld+json">{json.dumps(json_ld)}</script>
    </body></html>
    """


class FashionphileSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = FashionphileSpider()

    def test_is_tracked_brand(self):
        self.assertTrue(self.spider._is_tracked_brand("Hermes"))
        self.assertTrue(self.spider._is_tracked_brand("Christian Dior"))
        self.assertTrue(self.spider._is_tracked_brand("Chanel"))
        self.assertTrue(self.spider._is_tracked_brand("Gucci"))
        self.assertFalse(self.spider._is_tracked_brand("Coach"))
        self.assertFalse(self.spider._is_tracked_brand(None))

    def test_parse_collection_filters_and_requests_tracked_brands_only(self):
        products = [
            {"vendor": "Chanel", "handle": "chanel-flap-123"},
            {"vendor": "Coach", "handle": "coach-bag-456"},
            {"vendor": "Hermes", "handle": "hermes-birkin-789"},
        ]
        response = _collection_response(products, page=1)
        requests = [
            r for r in self.spider.parse_collection(response) if not isinstance(r, ListingItem)
        ]
        urls = {r.url for r in requests if hasattr(r, "url")}
        self.assertIn("https://www.fashionphile.com/products/chanel-flap-123", urls)
        self.assertIn("https://www.fashionphile.com/products/hermes-birkin-789", urls)
        self.assertNotIn("https://www.fashionphile.com/products/coach-bag-456", urls)

    def test_parse_product_extracts_json_ld_and_condition(self):
        json_ld = {
            "@context": "http://schema.org/",
            "@type": "Product",
            "name": "Hermes Togo Birkin 30 Gold",
            "url": "https://www.fashionphile.com/products/hermes-birkin-30-gold-99",
            "sku": "99",
            "brand": {"@type": "Brand", "name": "Hermes"},
            "offers": [{"@type": "Offer", "price": 18200.0, "priceCurrency": "USD"}],
        }
        html = _product_html(json_ld, 'This product\'s condition is "Excellent".')
        response = _product_response(
            "https://www.fashionphile.com/products/hermes-birkin-30-gold-99",
            html,
            vendor="Hermes",
        )
        items = list(self.spider.parse_product(response))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["marketplace"], "fashionphile")
        self.assertEqual(item["source_listing_id"], "99")
        self.assertEqual(item["price_amount"], 18200.0)
        self.assertEqual(item["currency"], "USD")
        self.assertEqual(item["condition_raw"], "Excellent")
        self.assertEqual(item["attributes_raw"], {"brand": "Hermes"})

    def test_parse_product_skips_when_no_json_ld(self):
        html = "<html><body><p>no structured data here</p></body></html>"
        response = _product_response(
            "https://www.fashionphile.com/products/missing-data",
            html,
            vendor="Chanel",
        )
        items = list(self.spider.parse_product(response))
        self.assertEqual(items, [])

    def test_mock_items_count(self):
        items = list(self.spider._mock_items())
        self.assertEqual(len(items), 2)
        self.assertTrue(all(item["marketplace"] == "fashionphile" for item in items))


if __name__ == "__main__":
    unittest.main()
