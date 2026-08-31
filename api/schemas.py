from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelSummary(BaseModel):
    brand: str
    model: str
    listing_count: int
    min_price: Decimal | None = None
    avg_price: Decimal | None = None
    max_price: Decimal | None = None
    currency: str = "USD"
    last_price_observed_at: datetime | None = None


class ModelStats(ModelSummary):
    pass


class ListingSummary(BaseModel):
    listing_id: int
    title: str | None = None
    url: str
    image_url: str | None = None
    brand: str | None = None
    model: str | None = None
    size: str | None = None
    color: str | None = None
    leather: str | None = None
    condition_raw: str | None = None
    condition_normalized: str | None = None
    product_variant_id: int | None = None
    match_confidence: Decimal | None = None
    match_method: str | None = None
    match_evidence: dict[str, Any] = Field(default_factory=dict)
    price_amount: Decimal | None = None
    currency: str | None = None
    price_observed_at: datetime | None = None
    marketplace: str | None = None
    status: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class PricePoint(BaseModel):
    observed_at: datetime
    price_amount: Decimal
    currency: str
    price_type: str | None = None


class ListingDetail(ListingSummary):
    price_history: list[PricePoint] = Field(default_factory=list)


class InvestigationBenchmark(BaseModel):
    comparison_level: str
    matched_on: list[str]
    sample_size: int
    p25: Decimal
    median: Decimal
    p75: Decimal
    min_price: Decimal
    max_price: Decimal
    data_freshness: datetime | None = None
    percentile: Decimal | None = None
    delta_amount: Decimal
    delta_percent: Decimal | None = None
    verdict: Literal["below_typical", "within_typical", "above_typical"]


class InvestigationReport(BaseModel):
    status: Literal["ready", "insufficient_data"]
    listing: ListingDetail
    benchmark: InvestigationBenchmark | None = None
    explanation: str
    comparables: list[ListingSummary] = Field(default_factory=list)


class ListingsPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ListingSummary]


class DailyActivity(BaseModel):
    scrape_date: date
    listings_touched: int
    new_listings: int


class HealthResponse(BaseModel):
    status: str
    database: str
    model_stats: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FilterOptions(BaseModel):
    sizes: list[str]
    colors: list[str]
    leathers: list[str]
    conditions: list[str]
    most_common_color: str | None = None
    most_common_leather: str | None = None


class MetaResponse(BaseModel):
    last_scrape_at: datetime | None = None
