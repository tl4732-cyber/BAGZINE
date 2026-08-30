import hashlib
import json
from datetime import datetime, timezone

CONDITION_MAP = {
    "new with tags": "new",
    "new without tags": "like_new",
    "new with box": "new",
    "new without box": "like_new",
    "new": "new",
    "excellent": "excellent",
    "very good": "very_good",
    "good": "good",
    "fair": "fair",
    "poor": "poor",
    "like new": "like_new",
}

CONDITION_PATTERNS = [
    ("new", ("new with tags", "new with box", "brand new", "giftable")),
    ("like_new", ("new without tags", "new without box", "like new", "unused")),
    ("excellent", ("excellent", "pristine")),
    ("very_good", ("very good",)),
    ("good", ("pre-owned - good", "preowned - good", "used - good", "good condition")),
    ("fair", ("fair", "worn", "shows wear")),
    ("poor", ("poor", "for parts", "flawed")),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_condition(raw: str | None) -> str | None:
    if not raw:
        return "unknown"
    key = " ".join(raw.strip().lower().replace("_", " ").split())
    if key in CONDITION_MAP:
        return CONDITION_MAP[key]
    for normalized, phrases in CONDITION_PATTERNS:
        if any(phrase in key for phrase in phrases):
            return normalized
    return "unknown"


def compute_content_hash(fields: dict) -> str:
    payload = {
        k: fields.get(k)
        for k in (
            "title",
            "price_amount",
            "currency",
            "condition_normalized",
            "status",
            "attributes_raw",
        )
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
