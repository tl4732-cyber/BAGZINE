"""Rules for when a scraped listing should link to a product row."""

from __future__ import annotations

import re

from bags.title_parser import ParsedProduct, parse_title

# Titles matching these are not saved at all (DropItem in pipeline).
DROP_TITLE_PATTERNS: list[str] = [
    r"\borganizer\b",
    r"\borganiser\b",
]

# Titles matching these are accessories/parts, not the bag itself.
ACCESSORY_PATTERNS: list[str] = [
    r"\bcharm\b",
    r"\bcover\b",
    r"protective",
    r"\bsilicone\b",
    r"stud feet",
    r"gift box",
    r"empty box",
    r"\bbox\s+only\b",
    r"storage bag",
    r"shopping bag ribbon",
    r"\bribbon\b",
    r"\bclochette\b",
    r"\btirette\b",
    r"felt cover",
    r"\bquartz\b",
    r"\bpadlock\b",
    # Base shapers / purse inserts / liners sold to fit inside a bag.
    r"\binsert(?:s)?\b",
    r"\bshaper(?:s)?\b",
    r"\bbag\s+saver\b",
    r"\bpurse\s+liner\b",
    r"\b(?:bag|purse)\s+liner\b",
    # Small leather goods and hardware parts frequently mislabeled with the bag's name.
    r"\bbelt\s+buckle\b",
    r"\bbuckle\s+only\b",
    r"\bkey\s*holder\b",
    r"\bkeychain\b",
    r"\bkey\s+fob\b",
    r"\bcard\s*holder\b",
    r"\bcosmetic\s+pouch\b",
    r"\bmakeup\s+pouch\b",
    r"\btwilly\b",
    r"\bbandeau\b",
    r"\bluggage\s+tag\b",
    r"\breplacement\s+strap\b",
    r"\bstrap\s+only\b",
    r"\bauthentication\s+card\b",
    r"\bcare\s+kit\b",
    r"\bcleaning\s+kit\b",
    r"\bleather\s+conditioner\b",
]

# Words/phrases that indicate the listing is describing a real, physical handbag
# (color, leather, hardware, silhouette) rather than an accessory sold "for" one.
BAG_PHYSICAL_INDICATORS = re.compile(
    r"\b(hand\s*bag|handbag|shoulder\s+bag|crossbody|tote\s+bag|satchel|clutch|wallet\s+on\s+chain|"
    r"porosus|crocodile|alligator|ostrich|togo|epsom|clemence|lambskin|caviar|swift|courchevel|"
    r"chevre|ch[eè]vre|evergrain|box\s+leather|suede|velvet|nylon|canvas|denim|python|lizard|"
    r"shearling|patent|monogram|vinyl|leather|"
    r"quilted|turn\s*lock|chain\s+strap|"
    r"gold\s+hardware|silver\s+hardware|\bghw\b|\bshw\b|"
    r"black|white|red|pink|beige|brown|blue|green|grey|gray|navy|ivory|tan|orange|"
    r"purple|burgundy|noir|etoupe|[ée]toupe)\b",
    re.IGNORECASE,
)

# Generic accessory-for-a-bag phrasing, e.g. "Insert For Chanel Classic Flap",
# "Base Shaper For Louis Vuitton Neverfull". Catches accessories even when the
# title otherwise parses cleanly to a brand + model.
ACCESSORY_FOR_BAG_PATTERN = re.compile(
    r"\b(insert|shaper|saver|liner|organizer|organiser|cover|protector|charm|"
    r"buckle|keychain|key\s*holder|card\s*holder)\b.*\bfor\b",
    re.IGNORECASE,
)

# Prices below these values are review signals, never identity filters.
SUSPICIOUS_PRICE_USD: dict[tuple[str, str], float] = {
    ("Hermès", "Birkin"): 8000.0,
    ("Hermès", "Kelly"): 5000.0,
}

def _title_matches_patterns(title: str, patterns: list[str]) -> bool:
    normalized = title.lower()
    return any(re.search(pattern, normalized) for pattern in patterns)


def should_drop_listing(
    title: str | None,
    price_amount: float | None = None,
    parsed: ParsedProduct | None = None,
) -> bool:
    """Drop only clear junk/accessories or titles with no identifiable bag model."""
    if not title or not title.strip():
        return True
    if _title_matches_patterns(title, DROP_TITLE_PATTERNS):
        return True
    if is_likely_accessory(title):
        return True
    return (parsed or parse_title(title)) is None


def is_dust_bag_only(title: str | None) -> bool:
    """True when the listing is a dust bag / pouch, not a handbag.

    Real bag listings that happen to include a dust bag as an accessory almost
    always mention a physical attribute of the bag (color, leather, hardware,
    silhouette) *before* "dust bag" is mentioned, e.g. "...Black Quilted Flap
    Turn Lock Gold Chain Crossbody Bag Dust Bag". Dust-bag-only listings just
    name the brand/model/size and then "dust bag", e.g. "NEW 100% Authentic
    CHANEL SMALL Classic Flap Dust Bag ICOT1".
    """
    if not title:
        return False
    normalized = title.lower()
    dust_match = re.search(r"\bdust\s+bag\b", normalized)
    if not dust_match:
        return False

    dust_pos = dust_match.start()
    for match in BAG_PHYSICAL_INDICATORS.finditer(normalized):
        if match.start() < dust_pos:
            return False
    return True


def is_likely_accessory(title: str | None) -> bool:
    if not title:
        return False
    if is_dust_bag_only(title):
        return True
    if _title_matches_patterns(title, ACCESSORY_PATTERNS):
        return True
    return bool(ACCESSORY_FOR_BAG_PATTERN.search(title.lower()))


def has_variant_detail(parsed: ParsedProduct) -> bool:
    """Require at least one physical attribute so we don't create catch-all products."""
    return bool(parsed.leather or parsed.size or parsed.color)


def is_suspicious_price(parsed: ParsedProduct, price_amount: float | None) -> bool:
    floor = SUSPICIOUS_PRICE_USD.get((parsed.brand, parsed.model))
    if floor is None:
        return False
    if price_amount is None:
        return True
    return float(price_amount) < floor


def should_link_listing(
    title: str | None,
    price_amount: float | None,
    parsed: ParsedProduct | None = None,
) -> bool:
    if not title:
        return False
    if is_likely_accessory(title):
        return False

    resolved = parsed or parse_title(title)
    if resolved is None:
        return False
    if not has_variant_detail(resolved):
        return False
    return True
