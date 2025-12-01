#!/usr/bin/env bash
set -euo pipefail

# Build and push to Docker Hub: bropotato/richtato:<tag>
#
# Usage:
#   ./publish.sh [tag] [VITE_API_BASE_URL] [PLATFORMS]
#
# Examples:
#   ./publish.sh                                 # multi-arch cloud publish (default)
#   ./publish.sh latest /api                     # multi-arch with defaults
#   ./publish.sh react /api "linux/amd64"        # single arch (amd64 only)

TAG=${1:-latest}
VITE_API_BASE_URL=${2:-/api}
PLATFORMS=${3:-linux/amd64,linux/arm64}
IMAGE="bropotato/richtato:${TAG}"

echo "[publish] Building ${IMAGE} for ${PLATFORMS} with VITE_API_BASE_URL='${VITE_API_BASE_URL}'"

docker buildx build \
  -f Dockerfile \
  --build-arg VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
  --platform ${PLATFORMS} \
  -t "${IMAGE}" \
  --push \
  .

echo "[publish] Pushed ${IMAGE}"
