#!/usr/bin/env bash
# Start the local bank-sync agent on the host.
#
# The main Richtato stack stays in Docker (db/backend/frontend). Browser
# automation runs here on the desktop so headed sign-in can use the native
# display and scheduled downloads can reuse the same Playwright runtime.
#
# Run after every reboot, before connecting a bank:
#   ./scripts/bank_sync/start-headed.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -z "${XAUTHORITY:-}" || ! -f "$XAUTHORITY" ]]; then
  echo "Log into your desktop session first (XAUTHORITY is missing)." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Missing .env (need RICHTATO_RUNNER_TOKEN)." >&2
  exit 1
fi

# Load runner token without sourcing the whole .env (SECRET_KEY has spaces).
RICHTATO_RUNNER_TOKEN="$(
  grep -E '^RICHTATO_RUNNER_TOKEN=' .env | head -1 | cut -d= -f2- | tr -d "'\" "
)"
if [[ -z "$RICHTATO_RUNNER_TOKEN" ]]; then
  echo "RICHTATO_RUNNER_TOKEN missing from .env" >&2
  exit 1
fi
export RICHTATO_RUNNER_TOKEN
export RICHTATO_BASE_URL="${RICHTATO_BASE_URL_HOST:-http://localhost:8000}"
export PYTHONPATH="$ROOT"
export BANK_SYNC_POLL_SECONDS="${BANK_SYNC_POLL_SECONDS:-30}"
export BANK_SYNC_DOWNLOAD_ROOT="$ROOT/local_data/bank_sync_downloads"

VENV="$ROOT/scripts/bank_sync/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Creating bank-sync host venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r scripts/bank_sync/requirements.txt
  "$VENV/bin/playwright" install chromium
fi

xhost +local: >/dev/null

pkill -f "scripts.bank_sync.agent" 2>/dev/null || true
sleep 0.5
nohup "$VENV/bin/python" -m scripts.bank_sync.agent \
  >local_data/bank-sync-agent.log 2>&1 &
sleep 1
echo "Bank-sync agent started (log: local_data/bank-sync-agent.log)"

echo "Main app stays in Docker: docker compose up -d"
echo "Open Accounts -> Connect bank -> Open browser to sign in."
