#!/usr/bin/env python3
"""Re-parse listing titles and link (or unlink) product variant rows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scrapers"))
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from bags.product_linking import is_suspicious_price, should_drop_listing, should_link_listing
from bags.product_matching import get_or_create_variant
from bags.title_parser import match_product
from bags.utils import normalize_condition
from db.models import Listing, PriceObservation
from db.session import get_session_factory


def _latest_price(session, listing_id: int) -> float | None:
    row = session.execute(
        select(PriceObservation.price_amount)
        .where(PriceObservation.listing_id == listing_id)
        .order_by(PriceObservation.observed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return float(row) if row is not None else None


def main() -> int:
    Session = get_session_factory()
    linked = 0
    unlinked = 0

    with Session() as session:
        listings = session.execute(select(Listing)).scalars().all()
        for listing in listings:
            match = match_product(listing.title, listing.attributes_raw)
            parsed = match.product
            price = _latest_price(session, listing.id)
            listing.condition_normalized = normalize_condition(listing.condition_raw)
            listing.match_confidence = match.confidence
            listing.match_method = match.method
            evidence = dict(match.evidence)
            if parsed and is_suspicious_price(parsed, price):
                evidence["price_anomaly"] = {
                    "value": True,
                    "source": "review_rule",
                    "matched_text": f"ask={price}",
                }
            listing.match_evidence = evidence

            if should_drop_listing(listing.title, price, parsed) or not should_link_listing(
                listing.title, price, parsed
            ):
                listing.product_variant_id = None
                unlinked += 1
                continue

            variant = get_or_create_variant(session, parsed)
            listing.product_variant_id = variant.id
            linked += 1
        session.commit()

    print(f"Linked {linked} listings, left {unlinked} unlinked for review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
