import type {
  FilterOptions,
  InvestigationReport,
  ListingDetail,
  ListingsPage,
  MetaResponse,
  ModelSummary,
  PricePoint,
  SortOption,
} from "./types";

const API_BASE =
  import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

async function getStaticModels(): Promise<ModelSummary[]> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/models.json`);
  if (!response.ok) {
    throw new Error(`Static catalog ${response.status}`);
  }
  return response.json() as Promise<ModelSummary[]>;
}

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  if (!API_BASE) {
    throw new Error("Live API is not configured for this deployment");
  }
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getModels: () => {
    if (import.meta.env.VITE_API_URL) {
      return get<ModelSummary[]>("/models");
    }
    if (import.meta.env.PROD) {
      return getStaticModels();
    }
    return get<ModelSummary[]>("/models");
  },
  getMeta: () => get<MetaResponse>("/meta"),
  getListings: (params: {
    brand?: string;
    model?: string;
    size?: string;
    color?: string;
    leather?: string;
    condition?: string;
    sort?: SortOption;
    limit?: number;
    offset?: number;
  }) => get<ListingsPage>("/listings", params),
  getFilters: (params: { brand?: string; model?: string }) =>
    get<FilterOptions>("/filters", params),
  getListing: (id: number) => get<ListingDetail>(`/listings/${id}`),
  getInvestigation: (id: number) =>
    get<InvestigationReport>(`/listings/${id}/investigation`),
  getPrices: (id: number) => get<PricePoint[]>(`/listings/${id}/prices`),
};

export function formatMoney(amount: string | null | undefined, currency = "USD"): string {
  if (amount == null) return "—";
  const value = Number(amount);
  if (Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}
