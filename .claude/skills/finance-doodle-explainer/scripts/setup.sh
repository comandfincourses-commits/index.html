#!/usr/bin/env bash
# One-time setup for the finance-doodle-explainer skill.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ok() { printf "  [ok] %s\n" "$1"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "  [missing] $1 — $2"; MISSING=1; }; }
MISSING=0
need ffmpeg "install from https://ffmpeg.org (Windows: winget install ffmpeg)"
need node "install Node.js 18+ (https://nodejs.org)"
need python3 "install Python 3.9+" 2>/dev/null || need python "install Python 3.9+"
[ "$MISSING" = 1 ] && { echo "Install the missing tools and re-run."; exit 1; }
ok "ffmpeg, node, python present"
PY=$(command -v python3 || command -v python)
$PY -m pip install --quiet --upgrade numpy faster-whisper && ok "python: numpy, faster-whisper"
cd "$HERE"
if node -e "require('playwright')" 2>/dev/null || [ -d node_modules/playwright ]; then ok "playwright present"
else npm install --silent --no-audit --no-fund playwright@1.56.1 && ok "playwright installed"; fi
# Use a preinstalled Chromium when available; otherwise download one.
if [ -z "$PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD" ]; then npx --yes playwright install chromium >/dev/null && ok "chromium ready"; else ok "chromium preinstalled"; fi
echo "Setup complete."
