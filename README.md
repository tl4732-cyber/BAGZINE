# luxury_vintage_bag_price

Track luxury vintage handbag prices. **Phase 1** is Scrapy only — built step by step.

## Start here

Read **[PHASE1.md](PHASE1.md)** for the step-by-step plan.

### Step 1 (current)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-scrapers.txt
cd scrapers
scrapy list
```

### Step 2 — mock data

```bash
cd scrapers
scrapy crawl dev_sample -o out.json
```

### Step 3 — eBay API

```bash
cp .env.example .env   # add EBAY_CLIENT_ID and EBAY_CLIENT_SECRET
cd scrapers
scrapy crawl ebay_api -o out.json
```

Without `.env` credentials, `ebay_api` still writes 2 mock eBay listings so you can test the flow.

### Step 5 — The RealReal (Playwright) — blocked, do not use for live scraping

The RealReal serves a PerimeterX behavioral CAPTCHA ("Press & Hold") to every
request, including plain HTTP GETs with no rate limiting involved. This is
deliberate anti-bot protection, not a selector bug, and circumventing it would
violate their Terms of Service. The spider is kept only for offline/mock testing:

```bash
cd scrapers
scrapy crawl therealreal -a use_mock=1 -o out.json   # offline test only
```

### Step 5b — Fashionphile (public Shopify JSON API)

Fashionphile runs on Shopify and exposes the standard public, unauthenticated
`products.json` storefront feed — no bot protection, and robots.txt allows
crawling `/collections` and `/products`. No browser automation needed.

```bash
cd scrapers
scrapy crawl fashionphile -a use_mock=1 -o out.json   # offline test
scrapy crawl fashionphile -o out.json                 # live crawl
```

### Step 5 — The RealReal (Playwright)

```bash
pip install -r requirements-scrapers.txt
playwright install chromium
cd scrapers
scrapy crawl therealreal -a use_mock=1 -o out.json   # offline test
scrapy crawl therealreal -o out.json                 # live TRR
```

### Step 6 — Postgres (local Docker)

```bash
bash scripts/setup_db.sh
cd scrapers
scrapy crawl dev_sample
bash ../scripts/query_db.sh
```

Phase 1 scraping is complete. **Phase B** adds a read-only API:

```bash
bash scripts/run_api.sh
# docs: http://127.0.0.1:8000/docs
```

**Phase C** — dashboard (React + Vite):

```bash
# Terminal 1
bash scripts/run_api.sh

# Terminal 2
bash scripts/run_dashboard.sh
# open http://127.0.0.1:5173
```

API tests (Postgres must be running):

```bash
RUN_API_TESTS=1 python3 -m unittest api.tests.test_api -q
```

## AWS pipeline (Tier 2)

The daily crawl (`scripts/crawl_daily.sh`) can also run as a serverless pipeline on AWS instead
of/alongside your machine's cron job:

```
EventBridge (cron) --> Lambda (Scrapy: ebay_api + fashionphile) --> S3 (raw/bronze landing zone)
                                                                          |
                                                    scripts/load_from_s3.py (junk filtering,
                                                    product matching, Postgres upsert)
                                                                          |
                                                                     Postgres (local, unchanged)
```

Design notes:

- **Lambda never talks to Postgres.** It only runs the two browser-free spiders (`ebay_api`,
  `fashionphile`) using a DB-free Scrapy settings profile (`scrapers/bags/settings_lambda.py`) and
  writes validated-but-unfiltered items to S3 as one newline-delimited JSON object per run
  (`bags.pipelines.S3RawArchivePipeline`, off by default locally — enable by setting
  `S3_ARCHIVE_BUCKET`).
- **`scripts/load_from_s3.py`** pulls new objects from S3 and replays each item through the exact
  same junk-filtering (`JunkListingPipeline`), product-matching (`ProductLinkPipeline`), and
  upsert (`PostgresListingPipeline`, `PriceObservationPipeline`) stages the local crawl uses — the
  matching/business logic lives in one place regardless of where a listing was scraped.
- This intentionally keeps Postgres local/free rather than requiring RDS. S3, Lambda, ECR,
  EventBridge, and SNS all fit inside AWS's Always Free / 12-month Free Tier for a once-a-day job
  at this volume (roughly: 30 Lambda invocations/month against a 1M/month free tier, a few MB of
  S3 storage against 5 GB free, one container image well under the 500 MB ECR free tier).

Deploy steps, Terraform, and the Dockerfile live in:

- [`infra/terraform/`](infra/terraform/README.md) — S3 bucket, ECR repo, IAM role, Lambda
  function, EventBridge schedule, and an SNS+CloudWatch alarm for failure emails.
- [`Dockerfile.lambda`](Dockerfile.lambda) — the Lambda container image.

To test the S3 archive pipeline locally without AWS (uses [moto](https://github.com/getmoto/moto)
to mock S3):

```bash
cd scrapers
python -m pytest tests/test_s3_pipeline.py tests/test_load_from_s3.py -q
```
