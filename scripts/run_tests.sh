#!/usr/bin/env bash
#
# Run all unit and integration tests (backend + frontend).
#
# Usage:
#   ./scripts/run_tests.sh                # all tests, SQLite (fast, no services needed)
#   ./scripts/run_tests.sh backend        # backend only, SQLite
#   ./scripts/run_tests.sh frontend       # frontend only
#   ./scripts/run_tests.sh --pg           # all tests, backend against Docker PostgreSQL
#   ./scripts/run_tests.sh backend --pg   # backend only, against Docker PostgreSQL
#
# The --pg flag runs backend tests against the real PostgreSQL in Docker
# (requires `docker compose up db`). This catches DB-specific edge cases
# that SQLite misses (decimal precision, type strictness, constraints).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

USE_PG=false
SCOPE="all"

for arg in "$@"; do
  case "$arg" in
    --pg)      USE_PG=true ;;
    backend)   SCOPE="backend" ;;
    frontend)  SCOPE="frontend" ;;
    all)       SCOPE="all" ;;
    -h|--help)
      echo "Usage: $0 [all|backend|frontend] [--pg]"
      echo ""
      echo "  all       Run backend + frontend tests (default)"
      echo "  backend   Run backend tests only"
      echo "  frontend  Run frontend tests only"
      echo "  --pg      Run backend tests against Docker PostgreSQL instead of SQLite"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [all|backend|frontend] [--pg]"
      exit 1
      ;;
  esac
done

BACKEND_OK=""
FRONTEND_OK=""

run_backend() {
  cd "$ROOT/backend"

  if [ "$USE_PG" = true ]; then
    echo -e "${BOLD}=== Backend Tests (pytest → PostgreSQL) ===${NC}"

    if ! docker compose -f "$ROOT/docker-compose.yml" ps db 2>/dev/null | grep -q "running"; then
      echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
      docker compose -f "$ROOT/docker-compose.yml" up -d db
      echo "Waiting for PostgreSQL to be ready..."
      until docker compose -f "$ROOT/docker-compose.yml" exec -T db pg_isready -U richtato >/dev/null 2>&1; do
        sleep 1
      done
    fi

    if DJANGO_SETTINGS_MODULE=richtato.test_pg_settings python -m pytest apps/ -v --tb=short; then
      BACKEND_OK="pass"
    else
      BACKEND_OK="fail"
    fi
  else
    echo -e "${BOLD}=== Backend Tests (pytest → SQLite in-memory) ===${NC}"
    if DJANGO_SETTINGS_MODULE=richtato.test_settings python -m pytest apps/ -v --tb=short; then
      BACKEND_OK="pass"
    else
      BACKEND_OK="fail"
    fi
  fi
  echo ""
}

run_frontend() {
  echo -e "${BOLD}=== Frontend Tests (vitest) ===${NC}"
  cd "$ROOT/frontend"
  if npx vitest run; then
    FRONTEND_OK="pass"
  else
    FRONTEND_OK="fail"
  fi
  echo ""
}

case "$SCOPE" in
  backend)  run_backend ;;
  frontend) run_frontend ;;
  all)      run_backend; run_frontend ;;
esac

echo -e "${BOLD}═══════════════════════════════════${NC}"
FAILED=0

if [ -n "$BACKEND_OK" ]; then
  DB_LABEL="SQLite"
  [ "$USE_PG" = true ] && DB_LABEL="PostgreSQL"
  if [ "$BACKEND_OK" = "pass" ]; then
    echo -e "  ${GREEN}✓ Backend tests passed ($DB_LABEL)${NC}"
  else
    echo -e "  ${RED}✗ Backend tests FAILED ($DB_LABEL)${NC}"
    FAILED=1
  fi
fi

if [ -n "$FRONTEND_OK" ]; then
  if [ "$FRONTEND_OK" = "pass" ]; then
    echo -e "  ${GREEN}✓ Frontend tests passed${NC}"
  else
    echo -e "  ${RED}✗ Frontend tests FAILED${NC}"
    FAILED=1
  fi
fi

echo -e "${BOLD}═══════════════════════════════════${NC}"

exit $FAILED
