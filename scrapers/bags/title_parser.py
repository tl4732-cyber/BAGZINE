"""Extract brand, model, size, color, and leather from listing titles."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedProduct:
    brand: str
    model: str
    size: str | None = None
    color: str | None = None
    leather: str | None = None


@dataclass(frozen=True)
class MatchResult:
    product: ParsedProduct | None
    confidence: float
    field_confidence: dict[str, float]
    method: str
    evidence: dict[str, dict[str, Any]]


BRAND_ALIASES: list[tuple[str, str]] = [
    ("hermes", "Hermès"),
    ("hermès", "Hermès"),
    ("chanel", "Chanel"),
    ("louis vuitton", "Louis Vuitton"),
    ("lv", "Louis Vuitton"),
    ("gucci", "Gucci"),
    ("dior", "Dior"),
    ("fendi", "Fendi"),
    ("bottega veneta", "Bottega Veneta"),
    ("celine", "Celine"),
    ("céline", "Celine"),
    ("prada", "Prada"),
    ("saint laurent", "Saint Laurent"),
    ("ysl", "Saint Laurent"),
    ("loewe", "Loewe"),
    ("goyard", "Goyard"),
]

# Longer model names first so "Classic Double Flap" wins over "Classic Flap".
MODEL_PATTERNS: list[tuple[str, str]] = [
    ("Classic Double Flap", r"classic\s+double\s+flap|double\s+flap"),
    (
        "Classic Flap",
        r"classic\s+flap|reissue\s+2\.55|2\.55|\bcc\s+flap\b|\bsingle\s+flap\b",
    ),
    ("Boy Bag", r"\bboy\s+bag\b|\bboy\b"),
    ("Haut à Courroies", r"\bhac\b|haut\s+[àa]\s+courroies"),
    (
        "Vinyl Kelly",
        r"vinyl\s+kelly|kelly\s+vinyl|\bkelly\b.*\bvinyl\b|\bvinyl\b.*\bkelly"
        r"|\bkelly\b.*\bpvc\b|\bpvc\b.*\bkelly",
    ),
    ("Birkin", r"\bbirkin\b"),
    ("Kelly", r"\bkelly\b"),
    ("Constance", r"\bconstance\b"),
    ("Garden Party", r"\bgarden\s+party\b"),
    ("Picotin", r"\bpicotin\b"),
    ("Evelyne", r"\bevelyne\b"),
    ("Lindy", r"\blindy\b"),
    ("Neverfull", r"\bneverfull\b"),
    ("Speedy", r"\bspeedy\b"),
    ("Alma", r"\balma\b"),
    ("Pochette Métis", r"\bpochette\s+m[ée]tis\b"),
    ("Dionysus", r"\bdionysus\b"),
    ("Marmont", r"\bmarmont\b"),
    ("Jackie", r"\bjackie\b"),
    ("Baguette", r"\bbaguette\b"),
    ("Peekaboo", r"\bpeekaboo\b"),
    ("Classic Box", r"\bclassic\s+box\b"),
    ("Triomphe", r"\btriomphe\b"),
    ("Luggage", r"\bluggage\b"),
    ("Trio", r"\btrio\b"),
    ("Lady Dior", r"lady\s+dior"),
    ("Diorama", r"\bdiorama\b"),
    ("Book Tote", r"\bbook\s+tote\b"),
    ("Saddle", r"\bsaddle\b"),
    ("Caro", r"\bcaro\b"),
    ("Bobby", r"\bbobby\b"),
    ("Galleria", r"\bgalleria\b"),
    ("Re-Edition 2005", r"re-?edition\s*2005|re-?edition"),
    ("Cleo", r"\bcleo\b"),
    ("Cahier", r"\bcahier\b"),
    ("Sac de Jour", r"sac\s+de\s+jour"),
    ("Loulou", r"\blou\s*lou\b"),
    ("Niki", r"\bniki\b"),
    ("Kate", r"\bkate\b"),
    ("College", r"\bcollege\b"),
]

MODEL_BRANDS: dict[str, set[str]] = {
    "Classic Double Flap": {"Chanel"},
    "Classic Flap": {"Chanel"},
    "Boy Bag": {"Chanel"},
    "Haut à Courroies": {"Hermès"},
    "Vinyl Kelly": {"Hermès"},
    "Birkin": {"Hermès"},
    "Kelly": {"Hermès"},
    "Constance": {"Hermès"},
    "Garden Party": {"Hermès"},
    "Picotin": {"Hermès"},
    "Evelyne": {"Hermès"},
    "Lindy": {"Hermès"},
    "Neverfull": {"Louis Vuitton"},
    "Speedy": {"Louis Vuitton"},
    "Alma": {"Louis Vuitton"},
    "Pochette Métis": {"Louis Vuitton"},
    "Dionysus": {"Gucci"},
    "Marmont": {"Gucci"},
    "Jackie": {"Gucci"},
    "Baguette": {"Fendi"},
    "Peekaboo": {"Fendi"},
    "Classic Box": {"Celine"},
    "Triomphe": {"Celine"},
    "Luggage": {"Celine"},
    "Trio": {"Celine"},
    "Lady Dior": {"Dior"},
    "Diorama": {"Dior"},
    "Book Tote": {"Dior"},
    "Saddle": {"Dior"},
    "Caro": {"Dior"},
    "Bobby": {"Dior"},
    "Galleria": {"Prada"},
    "Re-Edition 2005": {"Prada"},
    "Cleo": {"Prada"},
    "Cahier": {"Prada"},
    "Sac de Jour": {"Saint Laurent"},
    "Loulou": {"Saint Laurent"},
    "Niki": {"Saint Laurent"},
    "Kate": {"Saint Laurent"},
    "College": {"Saint Laurent"},
}

LEATHER_ALIASES: list[tuple[str, str]] = [
    ("taurillon clemence", "Taurillon Clemence"),
    ("veau swift", "Swift"),
    ("clemence", "Clemence"),
    ("courchevel", "Courchevel"),
    ("caviar", "Caviar"),
    ("lambskin", "Lambskin"),
    ("chevre", "Chèvre"),
    ("chèvre", "Chèvre"),
    ("alligator", "Alligator"),
    ("crocodile", "Crocodile"),
    ("ostrich", "Ostrich"),
    ("ardennes", "Ardennes"),
    ("box leather", "Box"),
    ("epsom", "Epsom"),
    ("evergrain", "Evergrain"),
    ("suede", "Suede"),
    ("swift", "Swift"),
    ("togo", "Togo"),
    ("calf", "Calf"),
    ("calf leather", "Calf"),
    ("calfskin", "Calf"),
    ("pvc", "Vinyl"),
    ("vinyl", "Vinyl"),
    # Canvas/fabric "materials" (LV/Dior/Gucci monogram patterns, tweed, etc.)
    # are tracked in the leather field the same way vinyl is.
    ("damier ebene", "Damier Ebene"),
    ("damier azur", "Damier Azur"),
    ("damier", "Damier"),
    ("monogram empreinte", "Monogram Empreinte"),
    ("empreinte", "Empreinte"),
    ("monogram", "Monogram"),
    ("canvas", "Canvas"),
    ("tweed", "Tweed"),
    ("velvet", "Velvet"),
    ("denim", "Denim"),
    ("python", "Python"),
    ("lizard", "Lizard"),
    ("nylon", "Nylon"),
]

COLOR_ALIASES: list[tuple[str, str]] = [
    ("etoupe/beige", "Etoupe"),
    ("étoupe/beige", "Etoupe"),
    ("rouge tomate", "Rouge Tomate"),
    ("thalassa blue", "Thalassa Blue"),
    ("tanzanite blue", "Tanzanite Blue"),
    ("tanzanite", "Tanzanite Blue"),
    ("poppy orange", "Poppy Orange"),
    ("cascade tricolor", "Cascade Tricolor"),
    ("rose lipstick", "Rose Lipstick"),
    ("gris etain", "Gris Étain"),
    ("vert vertigo", "Vert Vertigo"),
    ("vert anglais", "Vert Anglais"),
    ("trench", "Trench"),
    ("rouge ash", "Rouge Ash"),
    ("bleu jean", "Bleu Jean"),
    ("anemone", "Anemone"),
    ("etain", "Etain"),
    ("ciel", "Ciel"),
    ("burgundy", "Burgundy"),
    ("etoupe", "Etoupe"),
    ("étoupe", "Etoupe"),
    ("pelouse", "Pelouse"),
    ("raisin", "Raisin"),
    ("noir", "Black"),
    ("black", "Black"),
    ("white", "White"),
    ("gold", "Gold"),
    ("beige", "Beige"),
    ("brown", "Brown"),
    ("red", "Red"),
    ("rouge", "Red"),
    ("blue", "Blue"),
    ("orange", "Orange"),
    ("pink", "Pink"),
    ("green", "Green"),
    ("grey", "Grey"),
    ("gray", "Grey"),
    ("purple", "Purple"),
    ("tan", "Tan"),
    ("navy", "Navy"),
    ("cream", "Cream"),
    ("ivory", "Ivory"),
    ("craie", "Craie"),
    ("vermillion", "Vermillion"),
    ("noisette", "Noisette"),
    ("cassis", "Cassis"),
    ("rose tyrien", "Rose Tyrien"),
    ("bleu glacier", "Bleu Glacier"),
    ("toile", "Toile"),
    ("fauve", "Fauve"),
    ("violet", "Violet"),
    ("multicolor", "Multicolor"),
    ("multicolore", "Multicolor"),
    ("greige", "Greige"),
]

SIZE_PATTERN = re.compile(
    r"\b(mini|small|medium|large|jumbo|maxi|pm|mm|gm|15|20|25|28|30|32|35|40|45|50)\b",
    re.IGNORECASE,
)
SIZE_GLUE_PATTERN = re.compile(r"\b(15|20|25|28|30|32|35|40|45|50)([a-z])", re.IGNORECASE)

# Strip hardware phrases so "Gold Hardware" is not parsed as bag color Gold.
HARDWARE_PHRASES = re.compile(
    r"\b(?:gold|silver|palladium|rose gold|gunmetal)[\s-]*(?:tone\s+)?hardware\b"
    r"|\b(?:gold|silver|palladium)\s+tone\b"
    r"|\b(?:gold|silver|palladium)\s+metal\s+fittings\b",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text).lower()
    return lowered.encode("ascii", "ignore").decode("ascii")


def _find_alias(
    text: str,
    aliases: list[tuple[str, str]],
    *,
    word_boundary: bool = False,
) -> str | None:
    for needle, canonical in sorted(aliases, key=lambda pair: len(pair[0]), reverse=True):
        if word_boundary or len(needle) <= 4:
            if re.search(rf"\b{re.escape(needle)}\b", text):
                return canonical
        elif needle in text:
            return canonical
    return None


def _find_brand(text: str) -> str | None:
    return _find_alias(text, BRAND_ALIASES, word_boundary=True)


def _find_model(text: str) -> str | None:
    for canonical, pattern in MODEL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return canonical
    return None


def _find_size(text: str) -> str | None:
    match = SIZE_PATTERN.search(text)
    if not match:
        return None
    value = match.group(1).lower()
    if value in {"pm", "mm", "gm"}:
        return value.upper()
    if value.isdigit():
        return value
    return value.title()


def _expand_glued_tokens(text: str) -> str:
    """Split glued tokens like '35orange' or 'bluetogo'."""
    expanded = SIZE_GLUE_PATTERN.sub(r"\1 \2", text)
    for needle, _ in sorted(LEATHER_ALIASES, key=lambda pair: len(pair[0]), reverse=True):
        expanded = re.sub(
            rf"([a-z]){re.escape(needle)}",
            rf"\1 {needle}",
            expanded,
        )
    return expanded


def parse_title(title: str | None) -> ParsedProduct | None:
    """Return parsed bag identity when brand and model are found in the title."""
    if not title or not title.strip():
        return None

    normalized = _expand_glued_tokens(_normalize_text(title))
    brand = _find_brand(normalized)
    if not brand:
        return None

    model = _find_model(title)
    if not model:
        return None
    if brand not in MODEL_BRANDS.get(model, {brand}):
        return None

    size = _find_size(normalized)
    leather = _find_alias(normalized, LEATHER_ALIASES, word_boundary=True)

    color_text = HARDWARE_PHRASES.sub(" ", normalized)
    if leather:
        color_text = re.sub(rf"\b{re.escape(leather.lower())}\b", " ", color_text)
    color = _find_alias(color_text, COLOR_ALIASES, word_boundary=True)

    if model == "Vinyl Kelly" and leather is None:
        leather = "Vinyl"
    if model == "Vinyl Kelly" and color == "Vinyl":
        color = _find_alias(
            re.sub(r"\bvinyl\b", " ", color_text), COLOR_ALIASES, word_boundary=True
        )

    return ParsedProduct(
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
    )


def _aspect_values(aspects: dict[str, Any] | None) -> dict[str, str]:
    if not aspects:
        return {}
    values: dict[str, str] = {}
    for raw_key, raw_value in aspects.items():
        key = str(raw_key).strip().lower()
        if isinstance(raw_value, list):
            value = " ".join(str(item) for item in raw_value if item is not None)
        else:
            value = str(raw_value)
        if value.strip():
            values[key] = value.strip()
    return values


def _structured_product(aspects: dict[str, Any] | None) -> tuple[dict[str, str], dict[str, str]]:
    values = _aspect_values(aspects)
    extracted: dict[str, str] = {}
    matched_text: dict[str, str] = {}

    def first(keys: tuple[str, ...]) -> str | None:
        for key in keys:
            if key in values:
                return values[key]
        return None

    brand_text = first(("brand", "designer"))
    model_text = first(("model", "style", "product line"))
    size_text = first(("size", "bag width", "model size"))
    color_text = first(("color", "colour", "exterior color"))
    leather_text = first(("material", "exterior material", "leather"))

    candidates = {
        "brand": (_find_brand(_normalize_text(brand_text or "")), brand_text),
        "model": (_find_model(model_text or ""), model_text),
        "size": (_find_size(_normalize_text(size_text or "")), size_text),
        "color": (
            _find_alias(
                HARDWARE_PHRASES.sub(" ", _normalize_text(color_text or "")),
                COLOR_ALIASES,
                word_boundary=True,
            ),
            color_text,
        ),
        "leather": (
            _find_alias(
                _normalize_text(leather_text or ""),
                LEATHER_ALIASES,
                word_boundary=True,
            ),
            leather_text,
        ),
    }
    for field, (value, source_text) in candidates.items():
        if value:
            extracted[field] = value
            matched_text[field] = source_text or value
    return extracted, matched_text


def match_product(title: str | None, aspects: dict[str, Any] | None = None) -> MatchResult:
    """Match a listing using structured eBay aspects first and title text second."""
    title_product = parse_title(title)
    structured, structured_text = _structured_product(aspects)
    title_values = {
        field: getattr(title_product, field) if title_product else None
        for field in ("brand", "model", "size", "color", "leather")
    }

    values: dict[str, str | None] = {}
    field_confidence: dict[str, float] = {}
    evidence: dict[str, dict[str, Any]] = {}
    for field in ("brand", "model", "size", "color", "leather"):
        if structured.get(field):
            values[field] = structured[field]
            field_confidence[field] = 0.98
            evidence[field] = {
                "value": structured[field],
                "source": "structured_aspect",
                "matched_text": structured_text[field],
            }
        elif title_values[field]:
            values[field] = title_values[field]
            confidence = 0.95 if field in {"brand", "model"} else 0.82
            field_confidence[field] = confidence
            evidence[field] = {
                "value": title_values[field],
                "source": "title",
                "matched_text": title or "",
            }
        else:
            values[field] = None

    if (
        not values["brand"]
        or not values["model"]
        or values["brand"] not in MODEL_BRANDS.get(str(values["model"]), {str(values["brand"])})
    ):
        return MatchResult(
            product=None,
            confidence=0.0,
            field_confidence=field_confidence,
            method="unmatched",
            evidence=evidence,
        )

    known_variant_fields = sum(bool(values[field]) for field in ("size", "color", "leather"))
    identity_scores = [field_confidence["brand"], field_confidence["model"]]
    identity_scores.extend(
        field_confidence[field]
        for field in ("size", "color", "leather")
        if field in field_confidence
    )
    confidence = sum(identity_scores) / len(identity_scores)
    if known_variant_fields == 0:
        confidence = min(confidence, 0.60)
    elif known_variant_fields == 1:
        confidence = min(confidence, 0.78)

    method = "structured" if structured else "title"
    if structured and any(
        evidence.get(field, {}).get("source") == "title"
        for field in ("brand", "model", "size", "color", "leather")
    ):
        method = "hybrid"

    return MatchResult(
        product=ParsedProduct(
            brand=str(values["brand"]),
            model=str(values["model"]),
            size=values["size"],
            color=values["color"],
            leather=values["leather"],
        ),
        confidence=round(confidence, 3),
        field_confidence=field_confidence,
        method=method,
        evidence=evidence,
    )
