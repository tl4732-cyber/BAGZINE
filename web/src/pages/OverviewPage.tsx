import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { CatalogModelTile } from "../components/CatalogModelTile";
import { brandSectionId } from "../lib/modelImages";
import type { ModelSummary } from "../types";

const BRAND_ORDER = [
  "Bottega Veneta",
  "Celine",
  "Chanel",
  "Dior",
  "Fendi",
  "Goyard",
  "Gucci",
  "Hermès",
  "Loewe",
  "Louis Vuitton",
  "Prada",
  "Saint Laurent",
];

function scrollToBrand(brand: string) {
  const section = document.getElementById(brandSectionId(brand));
  if (!section) {
    return false;
  }
  section.scrollIntoView({ behavior: "smooth", block: "start" });
  return true;
}

export function OverviewPage() {
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [highlightBrand, setHighlightBrand] = useState("");
  const [query, setQuery] = useState("");

  const brandSections = useMemo(() => {
    const byBrand = new Map<string, ModelSummary[]>();
    for (const model of models) {
      const list = byBrand.get(model.brand) ?? [];
      list.push(model);
      byBrand.set(model.brand, list);
    }

    return Array.from(byBrand.entries())
      .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))
      .map(([brand, brandModels]) => ({
        brand,
        models: [...brandModels].sort((a, b) => b.listing_count - a.listing_count),
      }));
  }, [models]);

  const availableBrands = useMemo(
    () => new Set(brandSections.map((section) => section.brand)),
    [brandSections],
  );

  useEffect(() => {
    api
      .getModels()
      .then(setModels)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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

  function goToBrand(brand: string) {
    setHighlightBrand(brand);
    setQuery("");
    scrollToBrand(brand);
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) {
      return;
    }

    const exact = brandSections.find((section) => section.brand.toLowerCase() === trimmed);
    if (exact) {
      goToBrand(exact.brand);
      return;
    }

    const partial = brandSections.find((section) =>
      section.brand.toLowerCase().includes(trimmed),
    );
    if (partial) {
      goToBrand(partial.brand);
      return;
    }

    const marqueeMatch = BRAND_ORDER.find((brand) => brand.toLowerCase().includes(trimmed));
    if (marqueeMatch && availableBrands.has(marqueeMatch)) {
      goToBrand(marqueeMatch);
    }
  }

  return (
    <div className="catalog-page">
      <header className="catalog-toolbar">
        <div className="catalog-marquee">
          <nav className="catalog-tabs-track" aria-label="Brands">
            <div className="catalog-tabs">
              {BRAND_ORDER.map((brand) => (
                <button
                  key={brand}
                  type="button"
                  className={highlightBrand === brand ? "is-active" : undefined}
                  onClick={() => {
                    if (availableBrands.has(brand)) {
                      goToBrand(brand);
                    }
                  }}
                  disabled={!availableBrands.has(brand)}
                >
                  {brand}
                </button>
              ))}
            </div>
            <div className="catalog-tabs" aria-hidden="true">
              {BRAND_ORDER.map((brand) => (
                <button
                  key={`duplicate-${brand}`}
                  type="button"
                  tabIndex={-1}
                  disabled={!availableBrands.has(brand)}
                  onClick={() => {
                    if (availableBrands.has(brand)) {
                      goToBrand(brand);
                    }
                  }}
                >
                  {brand}
                </button>
              ))}
            </div>
          </nav>
        </div>

        <form className="catalog-controls" onSubmit={handleSearch}>
          <input
            type="search"
            className="catalog-search"
            placeholder="Search brand"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search brand"
          />
        </form>
      </header>

      <div className="catalog-directory">
        {brandSections.map((section) => (
          <section
            className="catalog-brand-section"
            key={section.brand}
            id={brandSectionId(section.brand)}
            aria-label={section.brand}
          >
            <h2 className="brand-watermark">{section.brand}</h2>
            <div className="catalog-model-grid">
              {section.models.map((model) => (
                <CatalogModelTile
                  key={`${model.brand}-${model.model}`}
                  model={model}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
