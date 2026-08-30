# SQL Analytics Views

Applied by Alembic migration `005_analytics_views.py`.

Run migrations:

```bash
bash scripts/setup_db.sh
# or: alembic -c db/alembic.ini upgrade head
```

Explore views:

```bash
bash scripts/query_analytics.sh
```

---

## v_latest_listing_prices

**Purpose:** Base view for the dashboard — one row per listing with its **latest** price and catalog attributes.

**Use for:**

- Listing browse table (title, url, price, brand, model, size, color, leather)
- Filtering listings before aggregation
- “View on eBay” links via `url`

**Key columns:** `listing_id`, `title`, `url`, `brand`, `model`, `size`, `color`, `leather`, `price_amount`, `currency`, `is_linked`

**Example:**

```sql
SELECT title, brand, model, price_amount, url
FROM v_latest_listing_prices
WHERE model = 'Birkin' AND is_linked
ORDER BY price_amount DESC
LIMIT 20;
```

---

## v_model_price_stats

**Purpose:** Summary cards on the homepage — **min / avg / max / count** per brand and model.

**Use for:**

- “Hermès Birkin: avg $14,056 (86 listings)” overview cards
- Model comparison (Birkin vs Kelly vs Classic Flap)

**Filters:** Only **linked**, **active** listings with a price.

**Example:**

```sql
SELECT brand, model, listing_count, min_price, avg_price, max_price
FROM v_model_price_stats
ORDER BY listing_count DESC;
```

---

## v_variant_price_stats

**Purpose:** Drill-down stats by **size, color, leather** within a model.

**Use for:**

- “Birkin 30 Togo Black” average price
- Filter panels on the dashboard (size/color/leather breakdown)

**Example:**

```sql
SELECT size, color, leather, listing_count, avg_price
FROM v_variant_price_stats
WHERE model = 'Birkin'
ORDER BY listing_count DESC;
```

---

## v_price_history

**Purpose:** Every price snapshot over time — powers **price trend charts**.

**Use for:**

- Listing detail page: price over time
- Detecting price drops on re-scrape

**Example:**

```sql
SELECT observed_at, price_amount, currency
FROM v_price_history
WHERE listing_id = 39
ORDER BY observed_at;
```

---

## v_daily_listing_activity

**Purpose:** Monitor the **daily auto-scrape** — how many listings were touched vs newly added each day.

**Use for:**

- Checking if `crawl_daily.sh` ran
- Ops/debugging scrape volume

**Example:**

```sql
SELECT *
FROM v_daily_listing_activity
ORDER BY scrape_date DESC
LIMIT 7;
```

---

## View dependency chain

```
listings + price_observations + product_variants
        └── v_latest_listing_prices
                 ├── v_model_price_stats
                 └── v_variant_price_stats

price_observations ──► v_price_history

listings ──► v_daily_listing_activity
```

