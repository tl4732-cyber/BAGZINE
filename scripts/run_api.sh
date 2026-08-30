#!/usr/bin/env bash
# Start the read-only FastAPI server (Phase B).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags}"
export PYTHONPATH="${ROOT}:${ROOT}/scrapers"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]] || ! "$PYTHON" -c "import sys" 2>/dev/null; then
  echo "Recreating broken .venv (project was moved off Desktop)..."
  rm -rf "$ROOT/.venv"
  python3 -m venv "$ROOT/.venv"
  PYTHON="$ROOT/.venv/bin/python"
fi

"$PYTHON" -m pip install -q -r requirements-api.txt

HOST="${API_HOST:-127.0.0.1}"
PORT="${API_PORT:-8000}"

echo "API docs: http://${HOST}:${PORT}/docs"
exec "$PYTHON" -m uvicorn api.main:app --host "$HOST" --port "$PORT" --reload
