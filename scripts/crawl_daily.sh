#!/usr/bin/env bash
# Daily eBay scrape: flagship models across Hermès, Chanel, Louis Vuitton,
# Gucci, Fendi, Celine, Dior, Prada, and Saint Laurent (see title_parser.py
# MODEL_PATTERNS/MODEL_BRANDS for the full recognized-model list). Also
# re-runs scripts/backfill_products.py after every crawl, so listings scraped
# under an older bags/title_parser.py or bags/product_linking.py rule set stay
# current, not just the ones just scraped.
# Run manually: bash scripts/crawl_daily.sh
# Schedule: bash scripts/install_daily_schedule.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs
LOG_FILE="${LOG_FILE:-logs/crawl_daily_$(date +%Y%m%d).log}"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Daily crawl started at $(date -Iseconds) ==="

export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags}"
CRAWL_LIMIT="${CRAWL_LIMIT:-100}"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

echo "Starting Postgres (Docker)..."
docker compose up -d

echo "Waiting for Postgres..."
for _ in {1..30}; do
  if docker compose exec -T postgres pg_isready -U lvbp -d luxury_bags >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker compose exec -T postgres pg_isready -U lvbp -d luxury_bags >/dev/null 2>&1; then
  echo "ERROR: Postgres not ready — aborting crawl."
  exit 1
fi

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]] || ! "$PYTHON" -c "import sys" 2>/dev/null; then
  echo "Recreating broken .venv..."
  rm -rf "$ROOT/.venv"
  python3 -m venv "$ROOT/.venv"
  PYTHON="$ROOT/.venv/bin/python"
  "$PYTHON" -m pip install -q -r requirements-scrapers.txt
fi

cd "$ROOT/scrapers"

# Leather-focused queries: exclude vinyl/PVC, wallets, and common junk from eBay
# results. One query per flagship model that title_parser.py can identify;
# add new lines here alongside new MODEL_PATTERNS/MODEL_BRANDS entries.
QUERIES=(
  # Hermès
  "Hermes Birkin leather handbag -vinyl -PVC -organizer -dust -candle -poster -silicone"
  "Hermes Kelly leather handbag Sellier Retourne -vinyl -PVC -organizer -cut -wallet -watch -quartz"
  "Hermes Constance bag -wallet -organizer -charm"
  # Chanel
  "Chanel classic flap bag -organizer"
  "Chanel Boy bag -wallet -organizer -charm"
  # Louis Vuitton
  "Louis Vuitton Neverfull bag -wallet -organizer -charm"
  "Louis Vuitton Speedy bag -wallet -organizer -charm"
  "Louis Vuitton Pochette Metis bag -wallet -organizer -charm"
  # Gucci
  "Gucci Marmont bag -wallet -organizer -charm"
  # Fendi
  "Fendi Baguette bag -wallet -organizer -charm"
  # Celine
  "Celine Luggage bag -wallet -organizer -charm"
  # Dior
  "Christian Dior Lady Dior bag -wallet -organizer -charm"
  "Christian Dior Saddle bag -wallet -organizer -charm"
  # Prada
  "Prada Galleria bag -wallet -organizer -charm"
  # Saint Laurent
  "Saint Laurent Loulou bag -wallet -organizer -charm"
)

for query in "${QUERIES[@]}"; do
  echo ""
  echo "--- Scraping: $query (limit=$CRAWL_LIMIT) ---"
  "$PYTHON" -m scrapy crawl ebay_api \
    -a query="$query" \
    -a limit="$CRAWL_LIMIT" \
    -a paginate=true \
    -s LOG_LEVEL=INFO
done

echo ""
echo "--- Re-linking listings against current parsing/matching rules ---"
# Cheap at this project's volume (thousands of rows) and keeps every listing's
# product_variant_id/match_confidence current even after a bags/title_parser.py
# or bags/product_linking.py rule change, not just newly-scraped rows. See
# scripts/backfill_products.py for what this re-derives and why it's safe to
# run repeatedly (it's idempotent — same input rules always produce the same
# links, regardless of how many times this has already run).
"$PYTHON" "$ROOT/scripts/backfill_products.py"

echo ""
echo "--- Summary ---"
docker compose exec -T postgres psql -U lvbp -d luxury_bags -c "
SELECT COUNT(*) AS total_listings FROM listings;
SELECT b.name AS brand, m.name AS model, COUNT(*) AS listings
FROM listings l
JOIN product_variants pv ON pv.id = l.product_variant_id
JOIN models m ON m.id = pv.model_id
JOIN brands b ON b.id = m.brand_id
GROUP BY b.name, m.name
ORDER BY b.name, m.name;
"

echo "=== Daily crawl finished at $(date -Iseconds) ==="
echo "Log: $ROOT/$LOG_FILE"
