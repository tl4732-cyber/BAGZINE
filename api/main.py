"""Read-only FastAPI — serves analytics views for the dashboard."""

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from api import queries
from api.deps import get_db
from api.schemas import (
    FilterOptions,
    HealthResponse,
    InvestigationReport,
    ListingDetail,
    ListingSummary,
    ListingsPage,
    MetaResponse,
    ModelStats,
    ModelSummary,
    PricePoint,
)

app = FastAPI(
    title="Luxury Bag Price API",
    version="0.1.0",
    description="Read-only endpoints over Postgres analytics views.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="ok", database="ok")
    except Exception:
        return HealthResponse(status="degraded", database="error")


@app.get("/models", response_model=list[ModelSummary], tags=["models"])
def list_models(db: Session = Depends(get_db)) -> list[ModelSummary]:
    """All tracked models with listing count and min/avg/max price."""
    return [ModelSummary(**row) for row in queries.fetch_models(db)]


@app.get("/stats", response_model=ModelStats, tags=["stats"])
def model_stats(
    model: str = Query(..., description="Model name, e.g. Birkin"),
    brand: str | None = Query(None, description="Brand name, e.g. Hermès"),
    db: Session = Depends(get_db),
) -> ModelStats:
    """Price summary for one model."""
    row = queries.fetch_stats(db, brand=brand, model=model)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No stats for model={model!r}")
    return ModelStats(**row)


@app.get("/meta", response_model=MetaResponse, tags=["meta"])
def meta(db: Session = Depends(get_db)) -> MetaResponse:
    return MetaResponse(last_scrape_at=queries.fetch_last_scrape_at(db))


@app.get("/filters", response_model=FilterOptions, tags=["listings"])
def listing_filters(
    brand: str | None = Query(None),
    model: str | None = Query(None),
    db: Session = Depends(get_db),
) -> FilterOptions:
    """Distinct size / color / leather values for browse filters."""
    options = queries.fetch_filter_options(db, brand=brand, model=model)
    return FilterOptions(**options)


@app.get("/listings", response_model=ListingsPage, tags=["listings"])
def list_listings(
    brand: str | None = Query(None),
    model: str | None = Query(None),
    size: str | None = Query(None),
    color: str | None = Query(None),
    leather: str | None = Query(None),
    condition: str | None = Query(None),
    sort: str = Query("price_desc", pattern="^(price_desc|price_asc|newest)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ListingsPage:
    """Filterable listing table backed by v_latest_listing_prices."""
    total = queries.count_listings(
        db,
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
        condition=condition,
    )
    items = queries.fetch_listings(
        db,
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
        condition=condition,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ListingsPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[ListingSummary(**row) for row in items],
    )


@app.get("/listings/{listing_id}/prices", response_model=list[PricePoint], tags=["listings"])
def listing_prices(listing_id: int, db: Session = Depends(get_db)) -> list[PricePoint]:
    """Price history for charts."""
    if queries.fetch_listing(db, listing_id) is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    rows = queries.fetch_price_history(db, listing_id)
    return [PricePoint(**row) for row in rows]


@app.get(
    "/listings/{listing_id}/investigation",
    response_model=InvestigationReport,
    tags=["listings"],
)
def listing_investigation(
    listing_id: int,
    db: Session = Depends(get_db),
) -> InvestigationReport:
    """Explain one listing's ask against the narrowest reliable comparable group."""
    row = queries.fetch_listing(db, listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    prices = queries.fetch_price_history(db, listing_id)
    result = queries.fetch_investigation(db, listing_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = ListingDetail(
        **row,
        price_history=[PricePoint(**point) for point in prices],
    )
    return InvestigationReport(
        status=result["status"],
        listing=listing,
        benchmark=result["benchmark"],
        explanation=result["explanation"],
        comparables=[ListingSummary(**item) for item in result["comparables"]],
    )


@app.get("/listings/{listing_id}", response_model=ListingDetail, tags=["listings"])
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> ListingDetail:
    """One listing with full price history."""
    row = queries.fetch_listing(db, listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    prices = queries.fetch_price_history(db, listing_id)
    return ListingDetail(
        **row,
        price_history=[PricePoint(**p) for p in prices],
    )
