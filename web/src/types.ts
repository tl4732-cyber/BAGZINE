export interface ModelSummary {
  brand: string;
  model: string;
  listing_count: number;
  min_price: string | null;
  avg_price: string | null;
  max_price: string | null;
  currency: string;
  last_price_observed_at: string | null;
}

export interface ListingSummary {
  listing_id: number;
  title: string | null;
  url: string;
  brand: string | null;
  model: string | null;
  size: string | null;
  color: string | null;
  leather: string | null;
  condition_raw: string | null;
  condition_normalized: string | null;
  product_variant_id: number | null;
  match_confidence: string | number | null;
  match_method: string | null;
  match_evidence: Record<
    string,
    { value?: string | boolean; source?: string; matched_text?: string }
  >;
  price_amount: string | null;
  currency: string | null;
  price_observed_at: string | null;
  marketplace: string | null;
  status: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

export interface PricePoint {
  observed_at: string;
  price_amount: string;
  currency: string;
  price_type: string | null;
}

export interface ListingDetail extends ListingSummary {
  price_history: PricePoint[];
}

export interface InvestigationBenchmark {
  comparison_level: string;
  matched_on: string[];
  sample_size: number;
  p25: string;
  median: string;
  p75: string;
  min_price: string;
  max_price: string;
  data_freshness: string | null;
  percentile: string | number | null;
  delta_amount: string;
  delta_percent: string | number | null;
  verdict: "below_typical" | "within_typical" | "above_typical";
}

export interface InvestigationReport {
  status: "ready" | "insufficient_data";
  listing: ListingDetail;
  benchmark: InvestigationBenchmark | null;
  explanation: string;
  comparables: ListingSummary[];
}

export interface ListingsPage {
  total: number;
  limit: number;
  offset: number;
  items: ListingSummary[];
}

export interface FilterOptions {
  sizes: string[];
  colors: string[];
  leathers: string[];
  conditions: string[];
}

export interface MetaResponse {
  last_scrape_at: string | null;
}

export type SortOption = "price_desc" | "price_asc" | "newest";
