"""Analytics SQL views for dashboard and reporting

Revision ID: 005
Revises: 004
Create Date: 2026-07-05

Views created (see db/analytics/VIEWS.md for full documentation):
  - v_latest_listing_prices   : one row per listing with latest price + catalog attrs
  - v_model_price_stats       : min/avg/max listing count per brand + model
  - v_variant_price_stats     : min/avg/max per brand + model + size/color/leather
  - v_price_history           : all price snapshots (for charts)
  - v_daily_listing_activity  : new vs re-scraped listings by day
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

V_LATEST_LISTING_PRICES = """
CREATE VIEW v_latest_listing_prices AS
SELECT
    l.id AS listing_id,
    l.title,
    l.url,
    l.status,
    l.first_seen_at,
    l.last_seen_at,
    mkt.code AS marketplace,
    b.name AS brand,
    mo.name AS model,
    pv.id AS product_variant_id,
    pv.size,
    pv.color,
    pv.leather,
    latest.price_amount,
    latest.currency,
    latest.observed_at AS price_observed_at,
    (l.product_variant_id IS NOT NULL) AS is_linked
FROM listings l
JOIN marketplaces mkt ON mkt.id = l.marketplace_id
LEFT JOIN product_variants pv ON pv.id = l.product_variant_id
LEFT JOIN models mo ON mo.id = pv.model_id
LEFT JOIN brands b ON b.id = mo.brand_id
LEFT JOIN LATERAL (
    SELECT price_amount, currency, observed_at
    FROM price_observations
    WHERE listing_id = l.id
    ORDER BY observed_at DESC
    LIMIT 1
) latest ON true
"""

V_MODEL_PRICE_STATS = """
CREATE VIEW v_model_price_stats AS
SELECT
    brand,
    model,
    currency,
    COUNT(*) AS listing_count,
    ROUND(MIN(price_amount)::numeric, 2) AS min_price,
    ROUND(AVG(price_amount)::numeric, 2) AS avg_price,
    ROUND(MAX(price_amount)::numeric, 2) AS max_price,
    MAX(price_observed_at) AS last_price_observed_at
FROM v_latest_listing_prices
WHERE is_linked
  AND price_amount IS NOT NULL
  AND status = 'active'
GROUP BY brand, model, currency
"""

V_VARIANT_PRICE_STATS = """
CREATE VIEW v_variant_price_stats AS
SELECT
    brand,
    model,
    size,
    color,
    leather,
    currency,
    COUNT(*) AS listing_count,
    ROUND(MIN(price_amount)::numeric, 2) AS min_price,
    ROUND(AVG(price_amount)::numeric, 2) AS avg_price,
    ROUND(MAX(price_amount)::numeric, 2) AS max_price,
    MAX(price_observed_at) AS last_price_observed_at
FROM v_latest_listing_prices
WHERE is_linked
  AND price_amount IS NOT NULL
  AND status = 'active'
GROUP BY brand, model, size, color, leather, currency
"""

V_PRICE_HISTORY = """
CREATE VIEW v_price_history AS
SELECT
    po.id AS price_observation_id,
    po.listing_id,
    po.observed_at,
    po.price_amount,
    po.currency,
    po.price_type,
    l.title,
    l.url,
    mkt.code AS marketplace,
    b.name AS brand,
    mo.name AS model,
    pv.size,
    pv.color,
    pv.leather
FROM price_observations po
JOIN listings l ON l.id = po.listing_id
JOIN marketplaces mkt ON mkt.id = l.marketplace_id
LEFT JOIN product_variants pv ON pv.id = l.product_variant_id
LEFT JOIN models mo ON mo.id = pv.model_id
LEFT JOIN brands b ON b.id = mo.brand_id
"""

V_DAILY_LISTING_ACTIVITY = """
CREATE VIEW v_daily_listing_activity AS
SELECT
    DATE(last_seen_at) AS scrape_date,
    COUNT(*) AS listings_touched,
    COUNT(*) FILTER (
        WHERE DATE(first_seen_at) = DATE(last_seen_at)
    ) AS new_listings
FROM listings
GROUP BY DATE(last_seen_at)
"""

VIEWS = [
    ("v_latest_listing_prices", V_LATEST_LISTING_PRICES),
    ("v_model_price_stats", V_MODEL_PRICE_STATS),
    ("v_variant_price_stats", V_VARIANT_PRICE_STATS),
    ("v_price_history", V_PRICE_HISTORY),
    ("v_daily_listing_activity", V_DAILY_LISTING_ACTIVITY),
]


def upgrade() -> None:
    for name, ddl in VIEWS:
        op.execute(ddl)


def downgrade() -> None:
    for name, _ in reversed(VIEWS):
        op.execute(f"DROP VIEW IF EXISTS {name}")
