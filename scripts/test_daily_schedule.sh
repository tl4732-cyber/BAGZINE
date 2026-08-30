#!/usr/bin/env bash
# Trigger the launchd job immediately and show where to check results.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.luxurybags.daily-scrape"
DOMAIN="gui/$(id -u)"

echo "Kickstarting ${LABEL}..."
launchctl kickstart -k "${DOMAIN}/${LABEL}"

sleep 3

echo ""
echo "--- launchd status ---"
launchctl print "${DOMAIN}/${LABEL}" 2>/dev/null | grep -E "state =|runs =|last exit" || true

echo ""
echo "--- launchd stderr (last 5 lines) ---"
tail -5 "$ROOT/logs/launchd_stderr.log" 2>/dev/null || echo "(no stderr log yet)"

echo ""
echo "--- today's crawl log ---"
TODAY_LOG="$ROOT/logs/crawl_daily_$(date +%Y%m%d).log"
if [[ -f "$TODAY_LOG" ]]; then
  tail -10 "$TODAY_LOG"
else
  echo "No $TODAY_LOG yet — if stderr shows 'Operation not permitted',"
  echo "move the repo off Desktop (see install_daily_schedule.sh output)."
fi
