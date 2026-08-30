#!/usr/bin/env bash
# Start the read-only FastAPI server (Phase B).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags}"
export PYTHONPATH="${ROOT}:${ROOT}/scrapers"

source .venv/bin/activate
pip install -q -r requirements-api.txt

HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"

echo "API docs: http://${HOST}:${PORT}/docs"
exec uvicorn api.main:app --host "$HOST" --port "$PORT" --reload
