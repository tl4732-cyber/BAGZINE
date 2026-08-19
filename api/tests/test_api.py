"""API integration tests (requires Postgres + migrated views)."""

import os
import unittest

from fastapi.testclient import TestClient

from api.main import app

SKIP = not os.environ.get("DATABASE_URL") and not os.getenv("RUN_API_TESTS")


@unittest.skipUnless(os.environ.get("RUN_API_TESTS"), "set RUN_API_TESTS=1 with Postgres running")
class ApiIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["database"], ("ok", "error"))

    def test_models(self):
        response = self.client.get("/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn("model", data[0])
            self.assertIn("listing_count", data[0])

    def test_stats_birkin(self):
        response = self.client.get("/stats", params={"model": "Birkin", "brand": "Hermès"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model"], "Birkin")
        self.assertGreater(body["listing_count"], 0)

    def test_listings_filter(self):
        response = self.client.get("/listings", params={"model": "Birkin", "limit": 5})
        self.assertEqual(response.status_code, 200)
        page = response.json()
        self.assertLessEqual(len(page["items"]), 5)
        self.assertGreaterEqual(page["total"], len(page["items"]))

    def test_listing_detail_and_prices(self):
        page = self.client.get("/listings", params={"limit": 1}).json()
        if not page["items"]:
            self.skipTest("no listings in database")
        listing_id = page["items"][0]["listing_id"]

        detail = self.client.get(f"/listings/{listing_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["listing_id"], listing_id)

        prices = self.client.get(f"/listings/{listing_id}/prices")
        self.assertEqual(prices.status_code, 200)
        self.assertIsInstance(prices.json(), list)

        investigation = self.client.get(f"/listings/{listing_id}/investigation")
        self.assertEqual(investigation.status_code, 200)
        report = investigation.json()
        self.assertIn(report["status"], ("ready", "insufficient_data"))
        self.assertEqual(report["listing"]["listing_id"], listing_id)
        self.assertNotIn(
            listing_id,
            [item["listing_id"] for item in report["comparables"]],
        )
        if report["status"] == "ready":
            self.assertGreaterEqual(report["benchmark"]["sample_size"], 5)
            self.assertIn(
                report["benchmark"]["verdict"],
                ("below_typical", "within_typical", "above_typical"),
            )


if __name__ == "__main__":
    unittest.main()
