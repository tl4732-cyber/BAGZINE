#!/usr/bin/env python3
"""Backfill listings.image_url from the eBay Browse API getItem endpoint."""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from sqlalchemy import select, text

from db.models import Listing, Marketplace
from db.session import get_session_factory


def _api_base() -> str:
    if os.getenv("EBAY_ENV", "sandbox") == "production":
        return "https://api.ebay.com"
    return "https://api.sandbox.ebay.com"


def _fetch_token() -> str:
    client_id = os.getenv("EBAY_CLIENT_ID", "")
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise SystemExit("Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env")

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }
    ).encode()
    request = urllib.request.Request(
        f"{_api_base()}/identity/v1/oauth2/token",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    token = payload.get("access_token")
    if not token:
        raise SystemExit(f"OAuth failed: {payload}")
    return token


def _image_from_item(payload: dict) -> str | None:
    image = payload.get("image")
    if isinstance(image, dict):
        url = image.get("imageUrl")
        if url:
            return str(url)
    thumbs = payload.get("thumbnailImages") or []
    if thumbs and isinstance(thumbs[0], dict):
        url = thumbs[0].get("imageUrl")
        if url:
            return str(url)
    additional = payload.get("additionalImages") or []
    if additional and isinstance(additional[0], dict):
        url = additional[0].get("imageUrl")
        if url:
            return str(url)
    return None


def _fetch_item_image(token: str, source_listing_id: str) -> str | None:
    encoded_id = urllib.parse.quote(source_listing_id, safe="")
    request = urllib.request.Request(
        f"{_api_base()}/buy/browse/v1/item/{encoded_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 410}:
            return None
        raise
    return _image_from_item(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Max listings to update (0 = all)")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds between API calls")
    args = parser.parse_args()

    token = _fetch_token()
    Session = get_session_factory()

    with Session() as session:
        ebay = session.execute(
            select(Marketplace).where(Marketplace.code == "ebay")
        ).scalar_one_or_none()
        if ebay is None:
            raise SystemExit("No ebay marketplace row found")

        query = (
            select(Listing)
            .where(
                Listing.marketplace_id == ebay.id,
                Listing.image_url.is_(None),
            )
            .order_by(Listing.id)
        )
        if args.limit > 0:
            query = query.limit(args.limit)
        listings = session.execute(query).scalars().all()

        updated = 0
        skipped = 0
        for index, listing in enumerate(listings, start=1):
            image_url = _fetch_item_image(token, listing.source_listing_id)
            if image_url:
                listing.image_url = image_url
                updated += 1
            else:
                skipped += 1

            if index % 25 == 0:
                session.commit()
                print(f"Processed {index}/{len(listings)}…")

            time.sleep(args.delay)

        session.commit()

    print(f"Done. Updated {updated} listings, skipped {skipped}.")


if __name__ == "__main__":
    main()
