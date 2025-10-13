#!/usr/bin/env bash
set -euo pipefail

# Build the single-service Docker image (frontend + backend + nginx)
#
# Usage:
#   ./build.sh [TAG] [VITE_API_BASE_URL]
#
# Examples:
#   ./build.sh richtato:latest /api
#   ./build.sh richtato:render https://your-app.onrender.com/api

IMAGE_TAG=${1:-richtato:latest}
VITE_API_BASE_URL=${2:-/api}

echo "[build] Building image '${IMAGE_TAG}' with VITE_API_BASE_URL='${VITE_API_BASE_URL}'"

docker build \
  -f Dockerfile \
  --build-arg VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
  -t "${IMAGE_TAG}" \
  .

echo "[build] Done. Image: ${IMAGE_TAG}"
