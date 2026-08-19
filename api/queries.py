"""Read-only SQL against analytics views."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

LISTING_BASE = """
SELECT
    listing_id,
    title,
    url,
    brand,
    model,
    size,
    color,
    leather,
    condition_raw,
    condition_normalized,
    product_variant_id,
    match_confidence,
    match_method,
    match_evidence,
    price_amount,
    currency,
    price_observed_at,
    marketplace,
    status,
    first_seen_at,
    last_seen_at
FROM v_latest_listing_prices
WHERE is_linked
"""


def fetch_models(session: Session) -> list[dict]:
    rows = session.execute(
        text(
            """
            SELECT brand, model, listing_count, min_price, avg_price, max_price,
                   currency, last_price_observed_at
            FROM v_model_price_stats
            ORDER BY brand, listing_count DESC, model
            """
        )
    )
    return [dict(row._mapping) for row in rows]


def fetch_stats(session: Session, *, brand: str | None, model: str) -> dict | None:
    query = """
        SELECT brand, model, listing_count, min_price, avg_price, max_price,
               currency, last_price_observed_at
        FROM v_model_price_stats
        WHERE model = :model
    """
    params: dict = {"model": model}
    if brand:
        query += " AND brand = :brand"
        params["brand"] = brand

    row = session.execute(text(query), params).mappings().first()
    return dict(row) if row else None


def count_listings(
    session: Session,
    *,
    brand: str | None,
    model: str | None,
    size: str | None,
    color: str | None,
    leather: str | None,
    condition: str | None,
) -> int:
    where, params = _listing_filters(
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
        condition=condition,
    )
    row = session.execute(
        text(f"SELECT COUNT(*) AS total FROM v_latest_listing_prices WHERE is_linked {where}"),
        params,
    ).one()
    return int(row.total)


def fetch_listings(
    session: Session,
    *,
    brand: str | None,
    model: str | None,
    size: str | None,
    color: str | None,
    leather: str | None,
    condition: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> list[dict]:
    where, params = _listing_filters(
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
        condition=condition,
    )
    order_by = _sort_clause(sort)
    params["limit"] = limit
    params["offset"] = offset
    rows = session.execute(
        text(
            f"""
            {LISTING_BASE}
            {where}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    return [dict(row._mapping) for row in rows]


def _sort_clause(sort: str) -> str:
    options = {
        "price_desc": "price_amount DESC NULLS LAST, listing_id",
        "price_asc": "price_amount ASC NULLS LAST, listing_id",
        "newest": "last_seen_at DESC NULLS LAST, listing_id",
    }
    return options.get(sort, options["price_desc"])


def fetch_filter_options(
    session: Session,
    *,
    brand: str | None,
    model: str | None,
) -> dict[str, list[str]]:
    where, params = _listing_filters(
        brand=brand,
        model=model,
        size=None,
        color=None,
        leather=None,
        condition=None,
    )

    def distinct(column: str) -> list[str]:
        rows = session.execute(
            text(
                f"""
                SELECT DISTINCT {column} AS value
                FROM v_latest_listing_prices
                WHERE is_linked AND {column} IS NOT NULL AND TRIM({column}) <> ''
                {where}
                ORDER BY value
                """
            ),
            params,
        )
        return [row.value for row in rows]

    return {
        "sizes": distinct("size"),
        "colors": distinct("color"),
        "leathers": distinct("leather"),
        "conditions": distinct("condition_normalized"),
    }


def fetch_last_scrape_at(session: Session):
    row = session.execute(
        text("SELECT MAX(last_seen_at) AS last_scrape_at FROM listings")
    ).mappings().first()
    return row["last_scrape_at"] if row else None


def _listing_filters(
    *,
    brand: str | None,
    model: str | None,
    size: str | None,
    color: str | None,
    leather: str | None,
    condition: str | None,
) -> tuple[str, dict]:
    clauses: list[str] = []
    params: dict = {}
    if brand:
        clauses.append("AND brand = :brand")
        params["brand"] = brand
    if model:
        clauses.append("AND model = :model")
        params["model"] = model
    if size:
        clauses.append("AND LOWER(size) = LOWER(:size)")
        params["size"] = size
    if color:
        clauses.append("AND LOWER(color) = LOWER(:color)")
        params["color"] = color
    if leather:
        clauses.append("AND LOWER(leather) = LOWER(:leather)")
        params["leather"] = leather
    if condition:
        clauses.append("AND condition_normalized = :condition")
        params["condition"] = condition
    return " ".join(clauses), params


def fetch_listing(session: Session, listing_id: int) -> dict | None:
    row = session.execute(
        text(
            f"""
            {LISTING_BASE}
            AND listing_id = :listing_id
            """
        ),
        {"listing_id": listing_id},
    ).mappings().first()
    return dict(row) if row else None


def fetch_price_history(session: Session, listing_id: int) -> list[dict]:
    rows = session.execute(
        text(
            """
            SELECT observed_at, price_amount, currency, price_type
            FROM v_price_history
            WHERE listing_id = :listing_id
            ORDER BY observed_at ASC
            """
        ),
        {"listing_id": listing_id},
    )
    return [dict(row._mapping) for row in rows]


MIN_COMPARABLES = 5


def _comparison_levels(target: dict) -> list[tuple[str, list[str]]]:
    blueprints = [
        ("exact_variant_condition", ["size", "leather", "color", "condition_normalized"]),
        ("size_leather_condition", ["size", "leather", "condition_normalized"]),
        ("size_condition", ["size", "condition_normalized"]),
        ("model_condition", ["condition_normalized"]),
        ("model", []),
    ]
    levels: list[tuple[str, list[str]]] = []
    seen: set[tuple[str, ...]] = set()
    for name, fields in blueprints:
        available = [
            field
            for field in fields
            if target.get(field) not in (None, "", "unknown")
        ]
        key = tuple(available)
        if key in seen:
            continue
        seen.add(key)
        levels.append((name, available))
    return levels


def _comparable_where(target: dict, fields: list[str]) -> tuple[str, dict]:
    clauses = [
        "AND listing_id <> :listing_id",
        "AND status = 'active'",
        "AND is_confident",
        "AND price_amount IS NOT NULL",
        "AND brand = :brand",
        "AND model = :model",
        "AND currency = :currency",
    ]
    params = {
        "listing_id": target["listing_id"],
        "brand": target["brand"],
        "model": target["model"],
        "currency": target["currency"],
        "target_price": target["price_amount"],
    }
    for field in fields:
        clauses.append(f"AND LOWER({field}) = LOWER(:{field})")
        params[field] = target[field]
    return "\n".join(clauses), params


def _fetch_comparable_stats(session: Session, target: dict, fields: list[str]) -> dict:
    where, params = _comparable_where(target, fields)
    row = session.execute(
        text(
            f"""
            SELECT
                COUNT(*) AS sample_size,
                ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_amount)::numeric, 2) AS p25,
                ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_amount)::numeric, 2) AS median,
                ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_amount)::numeric, 2) AS p75,
                ROUND(MIN(price_amount)::numeric, 2) AS min_price,
                ROUND(MAX(price_amount)::numeric, 2) AS max_price,
                MAX(price_observed_at) AS data_freshness,
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE price_amount <= :target_price)
                    / NULLIF(COUNT(*), 0),
                    1
                ) AS percentile
            FROM v_latest_listing_prices
            WHERE TRUE
            {where}
            """
        ),
        params,
    ).mappings().one()
    return dict(row)


def _fetch_comparables(
    session: Session,
    target: dict,
    fields: list[str],
    *,
    limit: int = 8,
) -> list[dict]:
    where, params = _comparable_where(target, fields)
    params["limit"] = limit
    rows = session.execute(
        text(
            f"""
            {LISTING_BASE}
            AND is_confident
            {where}
            ORDER BY ABS(price_amount - :target_price), last_seen_at DESC
            LIMIT :limit
            """
        ),
        params,
    )
    return [dict(row._mapping) for row in rows]


def fetch_investigation(session: Session, listing_id: int) -> dict | None:
    target = fetch_listing(session, listing_id)
    if target is None:
        return None

    if (
        not target.get("brand")
        or not target.get("model")
        or target.get("price_amount") is None
        or not target.get("currency")
    ):
        return {
            "status": "insufficient_data",
            "benchmark": None,
            "explanation": "BAGZINE could not identify enough listing attributes to build a comparison.",
            "comparables": [],
        }

    fallback_fields: list[str] = []
    for level_name, fields in _comparison_levels(target):
        fallback_fields = fields
        stats = _fetch_comparable_stats(session, target, fields)
        if int(stats["sample_size"]) < MIN_COMPARABLES:
            continue

        target_price = target["price_amount"]
        median = stats["median"]
        p25 = stats["p25"]
        p75 = stats["p75"]
        delta_amount = target_price - median
        delta_percent = (delta_amount / median * 100) if median else None
        if target_price < p25:
            verdict = "below_typical"
        elif target_price > p75:
            verdict = "above_typical"
        else:
            verdict = "within_typical"

        attribute_labels = {
            "size": "size",
            "leather": "leather",
            "color": "colour",
            "condition_normalized": "condition",
        }
        matched_on = [attribute_labels[field] for field in fields]
        scope = ", ".join(matched_on) if matched_on else "model"
        direction = "below" if delta_amount < 0 else "above"
        if delta_amount == 0:
            direction = "at"
        percent_text = f"{abs(float(delta_percent)):.1f}%" if delta_percent is not None else "0%"
        explanation = (
            f"Compared with {stats['sample_size']} active {target['model']} listings "
            f"matched on {scope}. This ask is {percent_text} {direction} the median asking price."
        )
        return {
            "status": "ready",
            "benchmark": {
                "comparison_level": level_name,
                "matched_on": matched_on,
                **stats,
                "delta_amount": delta_amount,
                "delta_percent": delta_percent,
                "verdict": verdict,
            },
            "explanation": explanation,
            "comparables": _fetch_comparables(session, target, fields),
        }

    comparables = _fetch_comparables(session, target, fallback_fields)
    return {
        "status": "insufficient_data",
        "benchmark": None,
        "explanation": (
            f"Fewer than {MIN_COMPARABLES} comparable active listings are available. "
            "BAGZINE will not estimate a typical asking-price range from this sample."
        ),
        "comparables": comparables,
    }
