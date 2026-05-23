#!/usr/bin/env bash
# Start headed bank-sync automation on Docker Desktop (TCP X11 bridge).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

mkdir -p local_data
if [[ -z "${XAUTHORITY:-}" || ! -f "$XAUTHORITY" ]]; then
  echo "XAUTHORITY is unset or missing; is a graphical session running?" >&2
  exit 1
fi

cp "$XAUTHORITY" local_data/.xauthority
xhost +local: >/dev/null

if pgrep -f "scripts/bank_sync/x11_bridge.py" >/dev/null; then
  echo "X11 bridge already running"
else
  nohup python3 scripts/bank_sync/x11_bridge.py >local_data/x11-bridge.log 2>&1 &
  sleep 1
  echo "X11 bridge started (log: local_data/x11-bridge.log)"
fi

docker compose -f docker-compose.yml -f docker-compose.x11.yml up -d automation
echo "Automation running in headed mode (DISPLAY=host.docker.internal:0)"
