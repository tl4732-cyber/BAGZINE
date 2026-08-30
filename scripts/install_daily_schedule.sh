#!/usr/bin/env bash
# Install a macOS launchd job to run crawl_daily.sh every day at 12:00.
#
# Usage:  bash scripts/install_daily_schedule.sh
# Test:   bash scripts/test_daily_schedule.sh
# Remove: bash scripts/uninstall_daily_schedule.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.luxurybags.daily-scrape"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
WRAPPER="$HOME/Library/Scripts/${LABEL}.sh"
CRAWL_SCRIPT="$ROOT/scripts/crawl_daily.sh"
LOG_DIR="$ROOT/logs"

# macOS blocks background launchd jobs from Desktop/Documents/Downloads (TCC).
# Symptom: logs/launchd_stderr.log shows "Operation not permitted", exit code 126.
is_protected_path() {
  case "$ROOT" in
    "$HOME/Desktop"/*|"$HOME/Documents"/*|"$HOME/Downloads"/*) return 0 ;;
    *) return 1 ;;
  esac
}

mkdir -p "$LOG_DIR" "$HOME/Library/Scripts"
chmod +x "$CRAWL_SCRIPT"

if is_protected_path; then
  echo "WARNING: Project is under a macOS protected folder:"
  echo "  $ROOT"
  echo ""
  echo "launchd CANNOT read Desktop/Documents/Downloads in the background."
  echo "Your schedule may fire at 12:00 but fail instantly (see logs/launchd_stderr.log)."
  echo ""
  echo "Fix (pick one):"
  echo "  1. RECOMMENDED — move the repo, then re-run this script:"
  echo "       mkdir -p ~/Projects"
  echo "       mv \"$ROOT\" ~/Projects/"
  echo "       cd ~/Projects/$(basename "$ROOT")"
  echo "       bash scripts/install_daily_schedule.sh"
  echo ""
  echo "  2. Grant Full Disk Access to /bin/bash:"
  echo "       System Settings → Privacy & Security → Full Disk Access → +"
  echo "       Press Cmd+Shift+G, enter: /bin/bash"
  echo "       Then: bash scripts/test_daily_schedule.sh"
  echo ""
  if [[ "${1:-}" != "--force" ]]; then
    echo "Re-run with --force to install anyway (will likely keep failing)."
    exit 1
  fi
  echo "Installing with --force (expect permission errors until you apply a fix above)."
  echo ""
fi

# Wrapper lives outside Desktop so launchd can at least start it.
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export HOME="${HOME}"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
exec /bin/bash "${CRAWL_SCRIPT}"
EOF
chmod +x "$WRAPPER"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${WRAPPER}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>12</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launchd_stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launchd_stderr.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME}</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

echo "Installed daily scrape schedule."
echo "  Plist:   $PLIST_PATH"
echo "  Wrapper: $WRAPPER"
echo "  Runs:    every day at 12:00 (laptop must be on and logged in)"
echo "  Script:  $CRAWL_SCRIPT"
echo ""
echo "Test now:  bash scripts/test_daily_schedule.sh"
echo "Manual:    bash scripts/crawl_daily.sh"
echo "Uninstall: bash scripts/uninstall_daily_schedule.sh"
