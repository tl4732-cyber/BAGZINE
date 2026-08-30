#!/usr/bin/env bash
set -euo pipefail

LABEL="com.luxurybags.daily-scrape"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
WRAPPER="$HOME/Library/Scripts/${LABEL}.sh"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
rm -f "$PLIST_PATH" "$WRAPPER"

echo "Removed daily scrape schedule."
