import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, formatMoney } from "../api";
import { ListingPhoto } from "../components/ListingPhoto";
import { getModelImage, PLACEHOLDER_IMAGE } from "../lib/modelImages";
import { scrollPageToTop } from "../lib/scrollToTop";
import type { FilterOptions, ListingSummary, ModelSummary, SortOption } from "../types";

const PAGE_SIZE = 50;

export function ModelExplorePage() {
  const { brand: brandParam, model: modelParam } = useParams();
  const brand = decodeURIComponent(brandParam ?? "");
  const model = decodeURIComponent(modelParam ?? "");
  const [searchParams, setSearchParams] = useSearchParams();

  const size = searchParams.get("size") ?? "";
  const color = searchParams.get("color") ?? "";
  const leather = searchParams.get("leather") ?? "";
  const condition = searchParams.get("condition") ?? "";
  const sort = (searchParams.get("sort") as SortOption) || "price_desc";
  const page = Number(searchParams.get("page") ?? "1");

  const [modelStats, setModelStats] = useState<ModelSummary | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({
    sizes: [],
    colors: [],
    leathers: [],
    conditions: [],
    most_common_color: null,
    most_common_leather: null,
  });
  const [items, setItems] = useState<ListingSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const offset = (page - 1) * PAGE_SIZE;
  const pendingScrollRef = useRef(true);

  useLayoutEffect(() => {
    pendingScrollRef.current = true;
    if (window.location.hash) {
      const url = `${window.location.pathname}${window.location.search}`;
      window.history.replaceState(window.history.state, "", url);
    }
    scrollPageToTop();
  }, [brand, model]);

  useEffect(() => {
    scrollPageToTop();
  }, [brand, model]);

  useEffect(() => {
    if (!loading && pendingScrollRef.current) {
      scrollPageToTop();
      pendingScrollRef.current = false;
    }
  }, [loading, brand, model]);

  useEffect(() => {
    api
      .getModels()
      .then((models) => {
        const match = models.find((m) => m.brand === brand && m.model === model) ?? null;
        setModelStats(match);
      })
      .catch(() => setModelStats(null));
  }, [brand, model]);

  useEffect(() => {
    api
      .getFilters({ brand, model })
      .then(setFilters)
      .catch(() =>
        setFilters({
          sizes: [],
          colors: [],
          leathers: [],
          conditions: [],
          most_common_color: null,
          most_common_leather: null,
        }),
      );
  }, [brand, model]);

  useEffect(() => {
    if (!brand || !model) return;
    setLoading(true);
    api
      .getListings({
        brand,
        model,
        size: size || undefined,
        color: color || undefined,
        leather: leather || undefined,
        condition: condition || undefined,
        sort,
        limit: PAGE_SIZE,
        offset,
      })
      .then((pageData) => {
        setItems(pageData.items);
        setTotal(pageData.total);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [brand, model, size, color, leather, condition, sort, offset]);

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currency = modelStats?.currency ?? "USD";
  const imageSrc = getModelImage(brand, model);

  const listingCount = modelStats?.listing_count ?? total;

  if (!brand || !model) {
    return (
      <section>
        <p className="error-text">Model not found.</p>
        <Link to="/prices" className="back-link">
          ← Back to brands
        </Link>
      </section>
    );
  }

  return (
    <section className="model-explore">
      <Link to="/prices" className="back-link model-explore-back">
        ← Back to brands
      </Link>

      <div className="model-explore-dashboard">
        <header className="model-explore-hero">
          <div className="model-explore-image">
            <img
              src={imageSrc}
              alt={`${brand} ${model}`}
              className="model-explore-photo"
              onError={(e) => {
                e.currentTarget.src = PLACEHOLDER_IMAGE;
              }}
            />
          </div>

          <div className="model-explore-info">
            <p className="model-explore-brand">{brand}</p>
            <h1 className="model-explore-title">{model}</h1>
            <p className="model-explore-price">{formatMoney(modelStats?.avg_price, currency)}</p>
            <p className="model-explore-description">
              Average resell price across {listingCount} listings.
            </p>

            <dl className="model-explore-stats">
              <div className="model-explore-stat">
                <dt>Min price</dt>
                <dd>{formatMoney(modelStats?.min_price, currency)}</dd>
              </div>
              <div className="model-explore-stat">
                <dt>Max price</dt>
                <dd>{formatMoney(modelStats?.max_price, currency)}</dd>
              </div>
              <div className="model-explore-stat">
                <dt>Listings</dt>
                <dd>{listingCount}</dd>
              </div>
              <div className="model-explore-stat">
                <dt>Most common color</dt>
                <dd>{filters.most_common_color ?? "—"}</dd>
              </div>
              <div className="model-explore-stat">
                <dt>Most common leather</dt>
                <dd>{filters.most_common_leather ?? "—"}</dd>
              </div>
            </dl>

            <button
              type="button"
              className="model-explore-cta"
              onClick={() => {
                document.getElementById("listings")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              View all listings
            </button>
          </div>
        </header>
      </div>

      <div id="listings" className="listings-panel">
        <div className="listings-panel-head">
          <h2>Available listings</h2>
          <p className="muted">{total} results</p>
        </div>

        <div className="filters">
          <label>
            Size
            <select value={size} onChange={(e) => updateParam("size", e.target.value)}>
              <option value="">All</option>
              {filters.sizes.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Color
            <select value={color} onChange={(e) => updateParam("color", e.target.value)}>
              <option value="">All</option>
              {filters.colors.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Leather
            <select value={leather} onChange={(e) => updateParam("leather", e.target.value)}>
              <option value="">All</option>
              {filters.leathers.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Condition
            <select
              value={condition}
              onChange={(e) => updateParam("condition", e.target.value)}
            >
              <option value="">All</option>
              {filters.conditions.map((v) => (
                <option key={v} value={v}>
                  {v.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sort
            <select value={sort} onChange={(e) => updateParam("sort", e.target.value)}>
              <option value="price_desc">Price: high to low</option>
              <option value="price_asc">Price: low to high</option>
              <option value="newest">Newest scraped</option>
            </select>
          </label>
        </div>

        {error && <p className="error-text">{error}</p>}
        {loading ? (
          <p className="page-status">Loading listings…</p>
        ) : (
          <div className="listings-grid">
            {items.map((item) => {
              const meta = [item.size, item.color, item.leather, item.condition_normalized]
                .filter(Boolean)
                .join(" · ");
              return (
                <article key={item.listing_id} className="listing-card">
                  <div className="listing-card-image">
                    <ListingPhoto
                      imageUrl={item.image_url}
                      alt={item.title ?? `${brand} ${model}`}
                    />
                  </div>
                  <div className="listing-card-body">
                    <Link to={`/listings/${item.listing_id}`} className="listing-card-title">
                      {item.title ?? "Untitled listing"}
                    </Link>
                    <p className="listing-card-meta">{meta || "—"}</p>
                    <p className="listing-card-price">
                      {formatMoney(item.price_amount, item.currency ?? "USD")}
                    </p>
                  </div>
                  <Link to={`/listings/${item.listing_id}`} className="listing-card-action">
                    <span>View investigation</span>
                    <span className="listing-card-arrow" aria-hidden>
                      →
                    </span>
                  </Link>
                </article>
              );
            })}
          </div>
        )}

        {!loading && items.length === 0 && (
          <p className="page-status">No listings match your filters.</p>
        )}

        {totalPages > 1 && (
          <div className="pagination">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => updateParam("page", String(page - 1))}
            >
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => updateParam("page", String(page + 1))}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
