import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatDate, formatMoney } from "../api";
import { PriceChart } from "../components/PriceChart";
import { getModelImage, modelExplorePath } from "../lib/modelImages";
import type { InvestigationReport } from "../types";

const VERDICT_LABELS = {
  below_typical: "Below the typical asking range",
  within_typical: "Within the typical asking range",
  above_typical: "Above the typical asking range",
};

function formatPercent(value: string | number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Math.abs(Number(value)).toFixed(1)}%`;
}

export function ListingDetailPage() {
  const { id } = useParams();
  const listingId = Number(id);
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!listingId) return;
    api
      .getInvestigation(listingId)
      .then(setReport)
      .catch((err: Error) => setError(err.message));
  }, [listingId]);

  const listing = report?.listing ?? null;
  const backHref =
    listing?.brand && listing.model
      ? modelExplorePath(listing.brand, listing.model)
      : "/prices";

  if (error) {
    return (
      <section>
        <p className="error-text">{error}</p>
        <Link to="/prices" className="back-link">
          ← Back to prices
        </Link>
      </section>
    );
  }

  if (!report || !listing) return <p className="page-status">Building investigation…</p>;

  const benchmark = report.benchmark;
  const price = Number(listing.price_amount ?? 0);
  const p25 = Number(benchmark?.p25 ?? 0);
  const p75 = Number(benchmark?.p75 ?? 0);
  const markerPosition =
    benchmark && p75 > p25
      ? Math.max(0, Math.min(100, ((price - p25) / (p75 - p25)) * 100))
      : 50;
  const confidence =
    listing.match_confidence == null ? null : Math.round(Number(listing.match_confidence) * 100);
  const imageSrc =
    listing.brand && listing.model
      ? getModelImage(listing.brand, listing.model)
      : "/images/bag-placeholder.svg";

  return (
    <section className="detail investigation">
      <Link to={backHref} className="back-link">
        ← Back to {listing.brand} {listing.model}
      </Link>

      <header className="investigation-hero">
        <div className="investigation-image">
          <img src={imageSrc} alt={`${listing.brand} ${listing.model}`} />
        </div>
        <div className="investigation-heading">
          <p className="eyebrow">
            BAGZINE Investigation #{listing.listing_id}
          </p>
          <h1>{listing.title ?? "Listing"}</h1>
          <p className="investigation-model">
            {listing.brand} · {listing.model}
          </p>
          <div className="detail-price">
            <p className="detail-price-label">Current asking price</p>
            <p className="detail-price-value">
              {formatMoney(listing.price_amount, listing.currency ?? "USD")}
            </p>
          </div>
          <a href={listing.url} target="_blank" rel="noreferrer" className="investigation-source">
            View original listing ↗
          </a>
        </div>
      </header>

      <section className={`investigation-verdict investigation-verdict--${benchmark?.verdict ?? "unknown"}`}>
        <p className="eyebrow">Finding</p>
        <h2>
          {benchmark ? VERDICT_LABELS[benchmark.verdict] : "Not enough evidence yet"}
        </h2>
        <p>{report.explanation}</p>
      </section>

      {benchmark && (
        <section className="investigation-benchmark">
          <div className="investigation-section-head">
            <div>
              <p className="eyebrow">Asking-price position</p>
              <h2>How this listing compares</h2>
            </div>
            <p className="muted">
              {benchmark.sample_size} comparables · updated {formatDate(benchmark.data_freshness)}
            </p>
          </div>

          <div className="price-position">
            <div className="price-position-track">
              <span className="price-position-marker" style={{ left: `${markerPosition}%` }} />
            </div>
            <div className="price-position-labels">
              <span>
                P25<br />
                {formatMoney(benchmark.p25, listing.currency ?? "USD")}
              </span>
              <span>
                Median<br />
                {formatMoney(benchmark.median, listing.currency ?? "USD")}
              </span>
              <span>
                P75<br />
                {formatMoney(benchmark.p75, listing.currency ?? "USD")}
              </span>
            </div>
          </div>

          <dl className="investigation-stats">
            <div>
              <dt>Difference from median</dt>
              <dd>{formatMoney(benchmark.delta_amount, listing.currency ?? "USD")}</dd>
            </div>
            <div>
              <dt>Percentage difference</dt>
              <dd>{formatPercent(benchmark.delta_percent)}</dd>
            </div>
            <div>
              <dt>Price percentile</dt>
              <dd>{formatPercent(benchmark.percentile)}</dd>
            </div>
            <div>
              <dt>Matched on</dt>
              <dd>{benchmark.matched_on.join(", ") || "model"}</dd>
            </div>
          </dl>
        </section>
      )}

      <section className="investigation-match">
        <div className="investigation-section-head">
          <div>
            <p className="eyebrow">What BAGZINE matched</p>
            <h2>Listing identity</h2>
          </div>
          <p className="match-confidence">
            {confidence == null ? "Unscored" : `${confidence}% confidence`}
          </p>
        </div>
        <dl className="detail-meta">
          <div>
            <dt>Size</dt>
            <dd>{listing.size ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Colour</dt>
            <dd>{listing.color ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Leather</dt>
            <dd>{listing.leather ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Condition</dt>
            <dd>{listing.condition_normalized?.replaceAll("_", " ") ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Match method</dt>
            <dd>{listing.match_method ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Last observed</dt>
            <dd>{formatDate(listing.last_seen_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="detail-chart">
        <p className="eyebrow">Listing history</p>
        <h2>Asking price over time</h2>
        <PriceChart points={listing.price_history} />
      </section>

      {report.comparables.length > 0 && (
        <section className="investigation-comparables">
          <div className="investigation-section-head">
            <div>
              <p className="eyebrow">Evidence</p>
              <h2>Nearest comparable listings</h2>
            </div>
          </div>
          <div className="comparable-grid">
            {report.comparables.map((item) => (
              <article className="comparable-card" key={item.listing_id}>
                <p className="comparable-card-model">
                  {item.brand} · {item.model}
                </p>
                <h3>{item.title ?? "Untitled listing"}</h3>
                <p className="comparable-card-attributes">
                  {[item.size, item.color, item.leather, item.condition_normalized]
                    .filter(Boolean)
                    .join(" · ") || "Attributes unavailable"}
                </p>
                <p className="comparable-card-price">
                  {formatMoney(item.price_amount, item.currency ?? "USD")}
                </p>
                <Link to={`/listings/${item.listing_id}`}>View investigation →</Link>
              </article>
            ))}
          </div>
        </section>
      )}

      <aside className="investigation-methodology">
        <p className="eyebrow">Methodology</p>
        <p>
          This report compares active eBay asking prices, not completed-sale values. BAGZINE uses
          the narrowest attribute group with at least five confidently matched listings. The
          typical range is the 25th–75th percentile and may change as listings appear or disappear.
        </p>
      </aside>
    </section>
  );
}
