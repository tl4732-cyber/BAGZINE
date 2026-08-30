import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, formatMoney } from "../api";
import type { FilterOptions, ListingSummary, ModelSummary, SortOption } from "../types";

const PAGE_SIZE = 50;

export function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const brand = searchParams.get("brand") ?? "";
  const model = searchParams.get("model") ?? "";
  const size = searchParams.get("size") ?? "";
  const color = searchParams.get("color") ?? "";
  const leather = searchParams.get("leather") ?? "";
  const sort = (searchParams.get("sort") as SortOption) || "price_desc";
  const page = Number(searchParams.get("page") ?? "1");

  const [models, setModels] = useState<ModelSummary[]>([]);
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

  const modelOptions = useMemo(() => {
    const seen = new Set<string>();
    return models.filter((m) => {
      const key = `${m.brand}::${m.model}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [models]);

  useEffect(() => {
    api.getModels().then(setModels).catch(() => setModels([]));
  }, []);

  useEffect(() => {
    api
      .getFilters({ brand: brand || undefined, model: model || undefined })
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
    setLoading(true);
    api
      .getListings({
        brand: brand || undefined,
        model: model || undefined,
        size: size || undefined,
        color: color || undefined,
        leather: leather || undefined,
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
  }, [brand, model, size, color, leather, sort, offset]);

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  }

  function onModelChange(value: string) {
    const selected = modelOptions.find((m) => `${m.brand}::${m.model}` === value);
    const next = new URLSearchParams();
    if (selected) {
      next.set("brand", selected.brand);
      next.set("model", selected.model);
    }
    if (sort !== "price_desc") next.set("sort", sort);
    setSearchParams(next);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Browse listings</h1>
          <p className="muted">{total} listings match your filters</p>
        </div>
      </div>

      <div className="filters">
        <label>
          Model
          <select
            value={brand && model ? `${brand}::${model}` : ""}
            onChange={(e) => onModelChange(e.target.value)}
          >
            <option value="">All models</option>
            {modelOptions.map((m) => (
              <option key={`${m.brand}-${m.model}`} value={`${m.brand}::${m.model}`}>
                {m.brand} {m.model}
              </option>
            ))}
          </select>
        </label>
        <label>
          Size
          <select value={size} onChange={(e) => updateParam("size", e.target.value)} disabled={!model}>
            <option value="">All</option>
            {filters.sizes.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Color
          <select value={color} onChange={(e) => updateParam("color", e.target.value)} disabled={!model}>
            <option value="">All</option>
            {filters.colors.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Leather
          <select value={leather} onChange={(e) => updateParam("leather", e.target.value)} disabled={!model}>
            <option value="">All</option>
            {filters.leathers.map((v) => (
              <option key={v} value={v}>{v}</option>
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
        <p className="muted">Loading listings…</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Price</th>
                <th>Size</th>
                <th>Color</th>
                <th>Leather</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.listing_id}>
                  <td>
                    <Link to={`/listings/${item.listing_id}`} className="title-link">
                      {item.title ?? "Untitled"}
                    </Link>
                  </td>
                  <td>{formatMoney(item.price_amount, item.currency ?? "USD")}</td>
                  <td>{item.size ?? "—"}</td>
                  <td>{item.color ?? "—"}</td>
                  <td>{item.leather ?? "—"}</td>
                  <td>
                    <a href={item.url} target="_blank" rel="noreferrer" className="ebay-link">
                      eBay
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
    </section>
  );
}
