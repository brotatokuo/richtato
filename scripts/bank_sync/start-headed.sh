#!/usr/bin/env bash
# Start the standalone bank-agent on the host in daemon mode.
#
# The agent is fully independent of the Richtato Docker stack. It owns
# its own SQLite vault under local_data/bank-agent/ and writes downloaded
# statement files directly into each account's storage_uri directory.
# The Richtato backend scanner (`python manage.py scan_statement_storage`)
# picks them up later and imports them.
#
# Setup (once):
#   1. Generate a Fernet key and add it to .env:
#        BANK_AGENT_FERNET_KEY="$(python -m scripts.bank_sync.agent generate-key)"
#   2. Edit scripts/bank_sync/bank_sync.yml with your logins and accounts, then:
#        python -m scripts.bank_sync.agent apply
#        python -m scripts.bank_sync.agent login signin <login_id>
#
# Run after every reboot to start the polling daemon:
#   ./scripts/bank_sync/start-headed.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -z "${XAUTHORITY:-}" || ! -f "$XAUTHORITY" ]]; then
  echo "Log into your desktop session first (XAUTHORITY is missing)." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Missing .env (need BANK_AGENT_FERNET_KEY)." >&2
  exit 1
fi

BANK_AGENT_FERNET_KEY="$(
  grep -E '^BANK_AGENT_FERNET_KEY=' .env | head -1 | cut -d= -f2- | tr -d "'\" "
)"
if [[ -z "$BANK_AGENT_FERNET_KEY" ]]; then
  echo "BANK_AGENT_FERNET_KEY missing from .env." >&2
  echo "Generate one with:  python -m scripts.bank_sync.agent generate-key" >&2
  exit 1
fi
export BANK_AGENT_FERNET_KEY
export PYTHONPATH="$ROOT"
export BANK_AGENT_POLL_SECONDS="${BANK_AGENT_POLL_SECONDS:-60}"

VENV="$ROOT/scripts/bank_sync/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Creating bank-sync host venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r scripts/bank_sync/requirements.txt
  "$VENV/bin/playwright" install chromium
fi

xhost +local: >/dev/null

pkill -f "scripts.bank_sync.agent run" 2>/dev/null || true
sleep 0.5

mkdir -p local_data
nohup "$VENV/bin/python" -m scripts.bank_sync.agent run \
  >local_data/bank-agent.log 2>&1 &
sleep 1
echo "bank-agent daemon started (log: local_data/bank-agent.log)"
echo ""
echo "Status:  python -m scripts.bank_sync.agent status"
echo "Sync:    python -m scripts.bank_sync.agent sync <login_id>"
echo "Signin:  python -m scripts.bank_sync.agent login signin <login_id>"
