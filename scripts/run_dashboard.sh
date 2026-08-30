#!/usr/bin/env bash
# Start the dashboard dev server (Phase C). Requires API on :8000.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/web"

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm not found. Install Node.js first."
  exit 1
fi

npm install
echo ""
echo "Dashboard: http://127.0.0.1:5173"
echo "API must be running: bash scripts/run_api.sh"
echo ""
exec npm run dev -- --host 127.0.0.1
