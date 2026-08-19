import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { ModelCard } from "../components/ModelCard";
import type { ModelSummary } from "../types";

const BRAND_ORDER = [
  "Celine",
  "Chanel",
  "Dior",
  "Hermès",
  "Louis Vuitton",
  "Prada",
  "Saint Laurent",
];

function sortBrands(brands: string[]): string[] {
  return [...brands].sort((a, b) => {
    const ai = BRAND_ORDER.indexOf(a);
    const bi = BRAND_ORDER.indexOf(b);
    if (ai !== -1 || bi !== -1) {
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    }
    return a.localeCompare(b);
  });
}

export function OverviewPage() {
  const [searchParams] = useSearchParams();
  const requestedBrand = searchParams.get("brand") ?? "";
  const initialBrand = BRAND_ORDER.includes(requestedBrand) ? requestedBrand : "";
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [brandFilter, setBrandFilter] = useState(initialBrand);
  const [brandView, setBrandView] = useState(Boolean(initialBrand));
  const [query, setQuery] = useState("");

  const brands = BRAND_ORDER;
  const trimmedQuery = query.trim().toLowerCase();
  const isSearching = trimmedQuery.length > 0;

  const filteredModels = useMemo(() => {
    let subset: ModelSummary[];
    if (isSearching) {
      // Search across every brand/model, not just the currently selected tab.
      subset = models.filter(
        (m) =>
          m.brand.toLowerCase().includes(trimmedQuery) ||
          m.model.toLowerCase().includes(trimmedQuery)
      );
    } else if (brandFilter) {
      subset = models.filter((m) => m.brand === brandFilter);
    } else {
      subset = [];
    }
    return subset.sort((a, b) => b.listing_count - a.listing_count).slice(0, isSearching ? 12 : 6);
  }, [models, brandFilter, isSearching, trimmedQuery]);

  useEffect(() => {
    api
      .getModels()
      .then((data) => {
        setModels(data);
        const available = sortBrands([...new Set(data.map((m) => m.brand))]);
        const preferredBrand = data.some((item) => item.brand === "Hermès")
          ? "Hermès"
          : available[0] || BRAND_ORDER[0];
        setBrandFilter((current) => current || preferredBrand);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!BRAND_ORDER.includes(requestedBrand)) return;
    setBrandFilter(requestedBrand);
    setBrandView(true);
    setQuery("");
  }, [requestedBrand]);

  if (loading) return <p className="page-status">Loading…</p>;
  if (error) {
    return (
      <div className="error-box">
        <p>Could not load data. Is the API running?</p>
        <code>bash scripts/run_api.sh</code>
        <p className="muted">{error}</p>
      </div>
    );
  }

  function selectBrand(brand: string) {
    setBrandFilter(brand);
    setBrandView(true);
    setQuery("");
  }

  return (
    <div className="catalog-page">
      {!brandView && (
        <header className="catalog-toolbar">
          <div className="catalog-marquee">
            <nav className="catalog-tabs-track" aria-label="Brands">
              <div className="catalog-tabs">
                {brands.map((brand) => (
                  <button
                    key={brand}
                    type="button"
                    className={brandFilter === brand ? "is-active" : undefined}
                    onClick={() => selectBrand(brand)}
                  >
                    {brand}
                  </button>
                ))}
              </div>
              <div className="catalog-tabs" aria-hidden="true">
                {brands.map((brand) => (
                  <button
                    key={`duplicate-${brand}`}
                    type="button"
                    tabIndex={-1}
                    onClick={() => selectBrand(brand)}
                  >
                    {brand}
                  </button>
                ))}
              </div>
            </nav>
          </div>

          <div className="catalog-controls">
            <input
              type="search"
              className="catalog-search"
              placeholder="Search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search models"
            />
          </div>
        </header>
      )}

      {brandFilter && (
        <section className={`brand-showcase${brandView ? " is-selected" : ""}`}>
          {brandView && (
            <button type="button" className="brand-return" onClick={() => setBrandView(false)}>
              ← Return
            </button>
          )}
          <h2 className="brand-watermark" aria-hidden>
            {isSearching ? `“${query.trim()}”` : brandFilter}
          </h2>

          <div className="catalog-grid">
            {filteredModels.map((model) => (
              <ModelCard
                key={`${model.brand}-${model.model}`}
                model={model}
                showBrand={isSearching}
              />
            ))}
          </div>

          {filteredModels.length === 0 && (
            <p className="page-status">
              {isSearching
                ? `No brands or models match “${query.trim()}”.`
                : "No models match your search."}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
