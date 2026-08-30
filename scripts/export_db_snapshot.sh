#!/usr/bin/env bash
# Export local Postgres data for importing into Neon (or any hosted Postgres).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/bagzine_snapshot.sql}"

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5433}"
PGUSER="${PGUSER:-lvbp}"
PGDATABASE="${PGDATABASE:-luxury_bags}"
export PGPASSWORD="${PGPASSWORD:-lvbp_dev}"

echo "Exporting $PGDATABASE from ${PGHOST}:${PGPORT} -> $OUT"
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  --no-owner --no-acl --clean --if-exists > "$OUT"
echo "Done. Import with: psql \"\$DATABASE_URL\" < $OUT"
