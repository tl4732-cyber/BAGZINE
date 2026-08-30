"""Investigation matching metadata and condition-aware analytics.

Revision ID: 006
Revises: 005
Create Date: 2026-07-13
"""

import importlib
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LATEST_VIEW = """
CREATE VIEW v_latest_listing_prices AS
SELECT
    l.id AS listing_id,
    l.title,
    l.url,
    l.status,
    l.condition_raw,
    l.condition_normalized,
    l.first_seen_at,
    l.last_seen_at,
    l.attributes_raw,
    l.match_confidence,
    l.match_method,
    l.match_evidence,
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
    (l.product_variant_id IS NOT NULL) AS is_linked,
    (
        l.product_variant_id IS NOT NULL
        AND COALESCE(l.match_confidence, 0) >= 0.70
    ) AS is_confident
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

MODEL_STATS_VIEW = """
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
WHERE is_confident
  AND price_amount IS NOT NULL
  AND status = 'active'
GROUP BY brand, model, currency
"""

VARIANT_STATS_VIEW = """
CREATE VIEW v_variant_price_stats AS
SELECT
    brand,
    model,
    size,
    color,
    leather,
    condition_normalized,
    currency,
    COUNT(*) AS listing_count,
    ROUND(MIN(price_amount)::numeric, 2) AS min_price,
    ROUND(AVG(price_amount)::numeric, 2) AS avg_price,
    ROUND(MAX(price_amount)::numeric, 2) AS max_price,
    MAX(price_observed_at) AS last_price_observed_at
FROM v_latest_listing_prices
WHERE is_confident
  AND price_amount IS NOT NULL
  AND status = 'active'
GROUP BY brand, model, size, color, leather, condition_normalized, currency
"""

PRICE_HISTORY_VIEW = """
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

DAILY_ACTIVITY_VIEW = """
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


def _drop_views() -> None:
    for name in (
        "v_daily_listing_activity",
        "v_price_history",
        "v_variant_price_stats",
        "v_model_price_stats",
        "v_latest_listing_prices",
    ):
        op.execute(f"DROP VIEW IF EXISTS {name}")


def _create_views() -> None:
    for ddl in (
        LATEST_VIEW,
        MODEL_STATS_VIEW,
        VARIANT_STATS_VIEW,
        PRICE_HISTORY_VIEW,
        DAILY_ACTIVITY_VIEW,
    ):
        op.execute(ddl)


def upgrade() -> None:
    _drop_views()
    op.add_column(
        "listings",
        sa.Column(
            "attributes_raw",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("listings", sa.Column("match_confidence", sa.Numeric(4, 3)))
    op.add_column("listings", sa.Column("match_method", sa.String(32)))
    op.add_column(
        "listings",
        sa.Column(
            "match_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index(
        "ix_listings_investigation",
        "listings",
        ["product_variant_id", "condition_normalized", "status"],
    )
    _create_views()


def downgrade() -> None:
    _drop_views()
    op.drop_index("ix_listings_investigation", table_name="listings")
    op.drop_column("listings", "match_evidence")
    op.drop_column("listings", "match_method")
    op.drop_column("listings", "match_confidence")
    op.drop_column("listings", "attributes_raw")

    previous = importlib.import_module("db.migrations.versions.005_analytics_views")
    for _, ddl in previous.VIEWS:
        op.execute(ddl)
