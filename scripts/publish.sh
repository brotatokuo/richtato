#!/usr/bin/env bash
set -euo pipefail

# Build and optionally push to Docker Hub: bropotato/richtato:<tag>
#
# Usage:
#   ./publish.sh [tag] [VITE_API_BASE_URL] [PLATFORMS] [--no-push]
#
# Examples:
#   ./publish.sh                                 # multi-arch build and push (default)
#   ./publish.sh latest /api                     # multi-arch with defaults
#   ./publish.sh react /api "linux/amd64"        # single arch (amd64 only)
#   ./publish.sh latest /api "linux/amd64" --no-push  # build only, don't push

TAG=${1:-latest}
VITE_API_BASE_URL=${2:-/api}
PLATFORMS=${3:-linux/amd64,linux/arm64}
PUSH_FLAG=${4:-}

# Check if --no-push is in any argument
NO_PUSH=false
for arg in "$@"; do
  if [ "$arg" = "--no-push" ]; then
    NO_PUSH=true
    break
  fi
done

IMAGE="bropotato/richtato:${TAG}"

if [ "$NO_PUSH" = true ]; then
  echo "[publish] Building ${IMAGE} for ${PLATFORMS} with VITE_API_BASE_URL='${VITE_API_BASE_URL}' (local build only)"
  docker buildx build \
    -f Dockerfile \
    --build-arg VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
    --platform ${PLATFORMS} \
    -t "${IMAGE}" \
    --load \
    .
  echo "[publish] Built ${IMAGE} (not pushed)"
else
  echo "[publish] Building ${IMAGE} for ${PLATFORMS} with VITE_API_BASE_URL='${VITE_API_BASE_URL}'"
  docker buildx build \
    -f Dockerfile \
    --build-arg VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
    --platform ${PLATFORMS} \
    -t "${IMAGE}" \
    --push \
    .
  echo "[publish] Pushed ${IMAGE}"
fi
