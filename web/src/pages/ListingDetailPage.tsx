import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatMoney } from "../api";
import { PriceChart } from "../components/PriceChart";
import { ListingPhoto } from "../components/ListingPhoto";
import { modelExplorePath } from "../lib/modelImages";
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

function formatSignedMoney(
  amount: string | number | null | undefined,
  currency = "USD",
): string {
  if (amount == null) return "—";
  const value = Number(amount);
  if (Number.isNaN(value)) return "—";
  const formatted = formatMoney(String(Math.abs(value)), currency);
  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return formatted;
}

function describeRangePosition(price: number, p25: number, p75: number, currency = "USD"): string {
  const formattedPrice = formatMoney(String(price), currency);
  if (price < p25) {
    return `This listing (${formattedPrice}) sits below the typical range (below P25).`;
  }
  if (price > p75) {
    return `This listing (${formattedPrice}) sits above the typical range (above P75).`;
  }
  return `This listing (${formattedPrice}) sits within the typical range (between P25 and P75).`;
}

const PRICE_RANGE_INSET = 15;

function computeListingMarkerPosition(price: number, p25: number, p75: number): number {
  const rangeStart = PRICE_RANGE_INSET;
  const rangeEnd = 100 - PRICE_RANGE_INSET;

  if (p75 <= p25) {
    return 50;
  }

  if (price < p25) {
    const ratio = Math.max(0, price / p25);
    return ratio * rangeStart;
  }

  if (price > p75) {
    const excess = (price - p75) / (p75 - p25);
    return Math.min(100, rangeEnd + excess * (100 - rangeEnd));
  }

  const ratio = (price - p25) / (p75 - p25);
  return rangeStart + ratio * (rangeEnd - rangeStart);
}

function TooltipHint({
  text,
  position = "above",
  alignRight = false,
}: {
  text: string;
  position?: "above" | "below";
  alignRight?: boolean;
}) {
  return (
    <span className="investigation-tooltip-trigger">
      <span className="investigation-tooltip-hint" aria-hidden="true">
        ?
      </span>
      <span
        className={`investigation-tooltip investigation-tooltip--${position}${
          alignRight ? " investigation-tooltip--align-right" : ""
        }`}
      >
        {text}
      </span>
    </span>
  );
}

function formatPercentileTooltip(
  percentile: string | number | null,
  sampleSize: number,
  model: string,
  matchedOn: string[],
): string {
  const value = percentile == null ? null : Math.round(Number(percentile));
  if (value == null || Number.isNaN(value)) {
    return "Percentile unavailable for this comparison.";
  }
  const scope =
    matchedOn.length > 0
      ? `matched on ${matchedOn.join(", ")}`
      : "matched on model";
  return `This listing is priced higher than about ${value}% of the ${sampleSize} ${model} listings ${scope}.`;
}

function formatDateOnly(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(new Date(iso));
}

function displayMeta(value: string | null | undefined): string {
  if (!value || value.toLowerCase() === "unknown") {
    return "—";
  }
  return value.replaceAll("_", " ");
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
  const listingMarkerPosition =
    benchmark && p75 > p25 ? computeListingMarkerPosition(price, p25, p75) : 50;
  const confidence =
    listing.match_confidence == null ? null : Math.round(Number(listing.match_confidence) * 100);
  const currency = listing.currency ?? "USD";
  const rangePosition =
    benchmark && p75 > p25 ? describeRangePosition(price, p25, p75, currency) : null;
  const percentileTooltip =
    benchmark && listing.model
      ? formatPercentileTooltip(
          benchmark.percentile,
          benchmark.sample_size,
          listing.model,
          benchmark.matched_on,
        )
      : null;

  return (
    <section className="detail investigation">
      <Link to={backHref} className="back-link">
        ← Back to {listing.brand} {listing.model}
      </Link>

      <header className="investigation-hero">
        <div className="investigation-image">
          <ListingPhoto
            imageUrl={listing.image_url}
            alt={listing.title ?? `${listing.brand} ${listing.model}`}
            className="investigation-photo"
            unavailableClassName="listing-photo-unavailable investigation-photo-unavailable"
          />
        </div>
        <div className="investigation-heading">
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
        <p className="investigation-verdict-explanation">{report.explanation}</p>
      </section>

      {benchmark && (
        <section className="investigation-benchmark">
          <div className="investigation-section-head">
            <div>
              <p className="eyebrow">Asking-price position</p>
              <h2>How this listing compares</h2>
            </div>
          </div>

          <div className="price-position">
            <div className="price-position-track">
              <span
                className="price-position-tick"
                style={{ left: `${PRICE_RANGE_INSET}%` }}
                aria-hidden="true"
              />
              <span className="price-position-tick" style={{ left: "50%" }} aria-hidden="true" />
              <span
                className="price-position-tick"
                style={{ left: `${100 - PRICE_RANGE_INSET}%` }}
                aria-hidden="true"
              />
              {rangePosition && (
                <span
                  className="price-position-listing-marker"
                  style={{ left: `${listingMarkerPosition}%` }}
                />
              )}
            </div>
            <div className="price-position-labels">
              <span
                className="price-position-label price-position-label--anchor"
                style={{ left: `${PRICE_RANGE_INSET}%` }}
              >
                <span className="price-position-label-title">
                  P25
                  <TooltipHint text="25% of comparables ask at or below this price" />
                </span>
                <br />
                {formatMoney(benchmark.p25, currency)}
              </span>
              <span
                className="price-position-label price-position-label--anchor price-position-label--anchor-center"
                style={{ left: "50%" }}
              >
                Median<br />
                {formatMoney(benchmark.median, currency)}
              </span>
              <span
                className="price-position-label price-position-label--anchor price-position-label--anchor-end"
                style={{ left: `${100 - PRICE_RANGE_INSET}%` }}
              >
                <span className="price-position-label-title">
                  P75
                  <TooltipHint
                    text="75% of comparables ask at or below this price"
                    alignRight
                  />
                </span>
                <br />
                {formatMoney(benchmark.p75, currency)}
              </span>
              {rangePosition && (
                <span
                  className={`price-position-label price-position-label--anchor price-position-label--listing${
                    listingMarkerPosition <= 20
                      ? " price-position-label--anchor-start"
                      : listingMarkerPosition >= 80
                        ? " price-position-label--anchor-end"
                        : ""
                  }`}
                  style={{ left: `${listingMarkerPosition}%` }}
                >
                  <span className="price-position-label-title">
                    This listing
                    <TooltipHint
                      text={rangePosition}
                      alignRight={listingMarkerPosition >= 70}
                    />
                  </span>
                  <br />
                  {formatMoney(listing.price_amount, currency)}
                </span>
              )}
            </div>
          </div>

          <div className="investigation-stats-row">
            <div className="investigation-stat-box investigation-stat-box--comparables">
              <p className="investigation-stat-label">Comparables</p>
              <p className="investigation-stat-value">{benchmark.sample_size}</p>
            </div>
            <dl className="investigation-stats">
              <div>
                <dt>Median</dt>
                <dd>{formatMoney(benchmark.median, currency)}</dd>
              </div>
              <div>
                <dt>Difference from median</dt>
                <dd>{formatSignedMoney(benchmark.delta_amount, currency)}</dd>
              </div>
              <div>
                <dt>
                  Price percentile
                  {percentileTooltip && (
                    <TooltipHint text={percentileTooltip} position="below" />
                  )}
                </dt>
                <dd>{formatPercent(benchmark.percentile)}</dd>
              </div>
              <div>
                <dt>Matched on</dt>
                <dd>{benchmark.matched_on.join(", ") || "model"}</dd>
              </div>
            </dl>
          </div>
        </section>
      )}

      <section className="investigation-match">
        <div className="investigation-section-head">
          <div>
            <p className="eyebrow">What matched</p>
            <h2>Listing identity</h2>
          </div>
          <p className="match-confidence">
            {confidence == null ? "Unscored" : `${confidence}% confidence`}
          </p>
        </div>
        <dl className="detail-meta">
          <div>
            <dt>Size</dt>
            <dd>{displayMeta(listing.size)}</dd>
          </div>
          <div>
            <dt>Colour</dt>
            <dd>{displayMeta(listing.color)}</dd>
          </div>
          <div>
            <dt>Leather</dt>
            <dd>{displayMeta(listing.leather)}</dd>
          </div>
          <div>
            <dt>Condition</dt>
            <dd>{displayMeta(listing.condition_normalized)}</dd>
          </div>
          <div>
            <dt>Match method</dt>
            <dd>{displayMeta(listing.match_method)}</dd>
          </div>
          <div>
            <dt>Last observed</dt>
            <dd>{formatDateOnly(listing.last_seen_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="detail-chart">
        <p className="eyebrow">Listing history</p>
        <h2 className="detail-chart-title">
          Asking price over time
          <TooltipHint
            text="When a changed price has been observed, it will be shown here"
            position="below"
          />
        </h2>
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
