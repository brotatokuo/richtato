#!/usr/bin/env bash
set -euo pipefail

# Run the single-container image locally, binding Nginx to the desired port.
#
# Usage:
#   ./start.sh [IMAGE_TAG] [PORT]
#
# Example:
#   ./start.sh richtato:latest 8080

IMAGE_TAG=${1:-richtato:latest}
PORT=${2:-10000}

echo "[start] Starting '${IMAGE_TAG}' on http://localhost:${PORT}"

docker run --rm -it \
  -e SECRET_KEY="dev-secret" \
  -e DEPLOY_STAGE="DEV" \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5433/richtato" \
  -e PORT="${PORT}" \
  -p "${PORT}:${PORT}" \
  "${IMAGE_TAG}"
