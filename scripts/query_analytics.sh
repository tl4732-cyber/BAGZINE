#!/usr/bin/env bash
# Print analytics view catalog and sample dashboard queries.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PSQL="docker compose exec -T postgres psql -U lvbp -d luxury_bags"

echo "=== Analytics views (db/analytics/VIEWS.md) ==="
echo ""
echo "  v_latest_listing_prices   — one row per listing + latest price (dashboard table)"
echo "  v_model_price_stats       — min/avg/max per brand + model (overview cards)"
echo "  v_variant_price_stats     — min/avg/max by size/color/leather (drill-down)"
echo "  v_price_history           — all price snapshots (charts)"
echo "  v_daily_listing_activity  — scrape volume by day (ops monitoring)"
echo ""

run_query() {
  echo "--- $1 ---"
  $PSQL -c "$2"
  echo ""
}

run_query "v_model_price_stats (dashboard overview)" \
  "SELECT brand, model, listing_count, min_price, avg_price, max_price, currency
   FROM v_model_price_stats
   ORDER BY listing_count DESC;"

run_query "v_daily_listing_activity (last 7 scrape days)" \
  "SELECT scrape_date, listings_touched, new_listings
   FROM v_daily_listing_activity
   ORDER BY scrape_date DESC
   LIMIT 7;"

run_query "linked listing count" \
  "SELECT COUNT(*) AS linked_listings FROM v_latest_listing_prices WHERE is_linked;"
