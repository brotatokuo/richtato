#!/usr/bin/env bash
#
# Smoke test: exercises the manual transaction and balance-update API paths
# against a running backend to verify nothing errors out.
#
# Usage:
#   ./scripts/smoke_test_api.sh                          # default: localhost:8000
#   ./scripts/smoke_test_api.sh http://localhost:9000     # custom base URL
#
# Prerequisites:
#   - Backend running (docker compose up -d)
#   - curl and jq installed
#
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
API="$BASE_URL/api/v1"
PASS=0
FAIL=0
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n" "$*"; }

assert_status() {
  local label="$1" expected="$2" actual="$3" body="$4"
  if [ "$actual" -eq "$expected" ]; then
    green "  ✓ $label (HTTP $actual)"
    PASS=$((PASS + 1))
  else
    red  "  ✗ $label — expected $expected, got $actual"
    red  "    $(echo "$body" | head -c 300)"
    FAIL=$((FAIL + 1))
  fi
}

assert_status_any() {
  local label="$1" actual="$2" body="$3"
  shift 3
  for code in "$@"; do
    if [ "$actual" -eq "$code" ]; then
      green "  ✓ $label (HTTP $actual)"
      PASS=$((PASS + 1))
      return
    fi
  done
  red  "  ✗ $label — got $actual, expected one of: $*"
  red  "    $(echo "$body" | head -c 300)"
  FAIL=$((FAIL + 1))
}

get_csrf() {
  grep csrftoken "$COOKIE_JAR" 2>/dev/null | awk '{print $NF}' || true
}

# Session-authenticated request (cookies + CSRF)
api() {
  local method="$1" path="$2"; shift 2
  curl -s -w "\n%{http_code}" \
    -X "$method" \
    -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $(get_csrf)" \
    -H "Referer: $BASE_URL/" \
    "$@" \
    "$API$path"
}

parse_response() {
  local raw="$1"
  BODY=$(echo "$raw" | sed '$d')
  HTTP_CODE=$(echo "$raw" | tail -1)
}

# ─── 0. Health check ────────────────────────────────────────────────────────
bold "=== Smoke Test: $BASE_URL ==="
echo ""
bold "0. Health check"
RAW=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/docs/" 2>/dev/null || echo -e "\n000")
parse_response "$RAW"
if [ "$HTTP_CODE" -eq 0 ] || [ "$HTTP_CODE" -eq 000 ]; then
  red "  ✗ Backend not reachable at $BASE_URL"
  red "    Start the backend first: docker compose up -d"
  exit 1
fi
assert_status_any "Backend reachable" "$HTTP_CODE" "$BODY" 200 301 302

# ─── 1. Authenticate via demo login ─────────────────────────────────────────
bold "1. Authenticate (demo login)"

# Get initial CSRF cookie
curl -s -b "$COOKIE_JAR" -c "$COOKIE_JAR" "$API/auth/csrf/" > /dev/null

RAW=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(get_csrf)" \
  -H "Referer: $BASE_URL/" \
  -d '{}' \
  "$API/auth/demo-login/")
parse_response "$RAW"
assert_status "Demo login" 200 "$HTTP_CODE" "$BODY"

SUCCESS=$(echo "$BODY" | jq -r '.success // false')
if [ "$SUCCESS" != "true" ]; then
  red "  Login failed — aborting."
  red "  Response: $(echo "$BODY" | head -c 300)"
  exit 1
fi
green "  Logged in as demo user"

# ─── 2. Create a test account ───────────────────────────────────────────────
bold "2. Create test account"
RAW=$(api POST "/accounts/" \
  -d "{
    \"name\": \"Smoke Test Checking\",
    \"account_type\": \"checking\",
    \"initial_balance\": 1000.00
  }")
parse_response "$RAW"
assert_status "Create account" 201 "$HTTP_CODE" "$BODY"

ACCOUNT_ID=$(echo "$BODY" | jq -r '.id // empty')
if [ -z "$ACCOUNT_ID" ]; then
  red "  Could not extract account ID — aborting."
  red "  Response: $(echo "$BODY" | head -c 300)"
  exit 1
fi
green "  Account ID: $ACCOUNT_ID"

# ─── 3. Fetch categories (pick an income & expense category) ────────────────
bold "3. Fetch categories"
RAW=$(api GET "/transactions/categories/")
parse_response "$RAW"
assert_status "List categories" 200 "$HTTP_CODE" "$BODY"

CATS=$(echo "$BODY" | jq -r 'if .categories then .categories else . end')
INCOME_CAT_ID=$(echo "$CATS" | jq -r '[.[] | select(.type=="income")][0].id // empty')
EXPENSE_CAT_ID=$(echo "$CATS" | jq -r '[.[] | select(.type=="expense")][0].id // empty')
green "  Income category ID: ${INCOME_CAT_ID:-none}"
green "  Expense category ID: ${EXPENSE_CAT_ID:-none}"

# ─── 4. Add an income transaction (credit) ──────────────────────────────────
bold "4. Add income transaction"
TODAY=$(date +%Y-%m-%d)

INCOME_PAYLOAD="{
  \"account_id\": $ACCOUNT_ID,
  \"date\": \"$TODAY\",
  \"amount\": 2500.00,
  \"description\": \"Smoke test salary\",
  \"transaction_type\": \"credit\"
}"
if [ -n "$INCOME_CAT_ID" ]; then
  INCOME_PAYLOAD=$(echo "$INCOME_PAYLOAD" | jq ". + {category_id: $INCOME_CAT_ID}")
fi

RAW=$(api POST "/transactions/" -d "$INCOME_PAYLOAD")
parse_response "$RAW"
assert_status "Create income transaction" 201 "$HTTP_CODE" "$BODY"

INCOME_TX_ID=$(echo "$BODY" | jq -r '.id // empty')
green "  Transaction ID: $INCOME_TX_ID"

# ─── 5. Add an expense transaction (debit) ──────────────────────────────────
bold "5. Add expense transaction"

EXPENSE_PAYLOAD="{
  \"account_id\": $ACCOUNT_ID,
  \"date\": \"$TODAY\",
  \"amount\": 85.50,
  \"description\": \"Smoke test groceries\",
  \"transaction_type\": \"debit\"
}"
if [ -n "$EXPENSE_CAT_ID" ]; then
  EXPENSE_PAYLOAD=$(echo "$EXPENSE_PAYLOAD" | jq ". + {category_id: $EXPENSE_CAT_ID}")
fi

RAW=$(api POST "/transactions/" -d "$EXPENSE_PAYLOAD")
parse_response "$RAW"
assert_status "Create expense transaction" 201 "$HTTP_CODE" "$BODY"

EXPENSE_TX_ID=$(echo "$BODY" | jq -r '.id // empty')
green "  Transaction ID: $EXPENSE_TX_ID"

# ─── 6. Verify account balance updated correctly ────────────────────────────
bold "6. Verify account balance"
RAW=$(api GET "/accounts/$ACCOUNT_ID/")
parse_response "$RAW"
assert_status "Get account detail" 200 "$HTTP_CODE" "$BODY"

BALANCE=$(echo "$BODY" | jq -r '.balance // empty')
EXPECTED="3414.50"  # 1000 + 2500 - 85.50
if [ "$BALANCE" = "$EXPECTED" ]; then
  green "  ✓ Balance correct: \$$BALANCE (expected \$$EXPECTED)"
  PASS=$((PASS + 1))
else
  red  "  ✗ Balance mismatch: got \$$BALANCE, expected \$$EXPECTED"
  FAIL=$((FAIL + 1))
fi

# ─── 7. Update the expense transaction ──────────────────────────────────────
bold "7. Update expense transaction"
RAW=$(api PATCH "/transactions/$EXPENSE_TX_ID/" \
  -d "{
    \"amount\": 120.00,
    \"description\": \"Smoke test groceries (updated)\"
  }")
parse_response "$RAW"
assert_status "Update transaction" 200 "$HTTP_CODE" "$BODY"

# Verify balance after update: 1000 + 2500 - 120 = 3380
RAW=$(api GET "/accounts/$ACCOUNT_ID/")
parse_response "$RAW"
BALANCE=$(echo "$BODY" | jq -r '.balance // empty')
EXPECTED="3380.00"
if [ "$BALANCE" = "$EXPECTED" ]; then
  green "  ✓ Balance after update: \$$BALANCE"
  PASS=$((PASS + 1))
else
  red  "  ✗ Balance after update: got \$$BALANCE, expected \$$EXPECTED"
  FAIL=$((FAIL + 1))
fi

# ─── 8. Set absolute balance (reconciliation) ───────────────────────────────
bold "8. Set absolute balance"
RAW=$(api POST "/accounts/details/" \
  -d "{
    \"account\": $ACCOUNT_ID,
    \"balance\": 5000.00,
    \"date\": \"$TODAY\"
  }")
parse_response "$RAW"
assert_status "Set absolute balance" 200 "$HTTP_CODE" "$BODY"

SET_BALANCE=$(echo "$BODY" | jq -r '.balance // empty')
# Normalize: strip trailing zeros after decimal for comparison
NORM_SET=$(echo "$SET_BALANCE" | awk '{printf "%.2f", $1}')
if [ "$NORM_SET" = "5000.00" ]; then
  green "  ✓ Balance set to \$$SET_BALANCE"
  PASS=$((PASS + 1))
else
  red  "  ✗ Expected 5000.00, got $SET_BALANCE"
  FAIL=$((FAIL + 1))
fi

# ─── 9. Verify balance history exists ───────────────────────────────────────
bold "9. Check balance history"
RAW=$(api GET "/accounts/$ACCOUNT_ID/balance-history/")
parse_response "$RAW"
assert_status "Get balance history" 200 "$HTTP_CODE" "$BODY"

HISTORY_COUNT=$(echo "$BODY" | jq '
  if type == "array" then length
  elif .data_points then (.data_points | length)
  elif .history then (.history | length)
  else 0 end')
if [ "$HISTORY_COUNT" -gt 0 ]; then
  green "  ✓ Balance history entries: $HISTORY_COUNT"
  PASS=$((PASS + 1))
else
  red  "  ✗ No balance history found"
  FAIL=$((FAIL + 1))
fi

# ─── 10. Get transaction summary ────────────────────────────────────────────
bold "10. Transaction summary"
MONTH_START=$(date +%Y-%m-01)
RAW=$(api GET "/transactions/summary/?start_date=$MONTH_START&end_date=$TODAY")
parse_response "$RAW"
assert_status "Transaction summary" 200 "$HTTP_CODE" "$BODY"

SUMMARY_NET=$(echo "$BODY" | jq -r '.net // empty')
if [ -n "$SUMMARY_NET" ]; then
  green "  Net: $SUMMARY_NET"
fi

# ─── 11. Get cashflow summary ───────────────────────────────────────────────
bold "11. Cashflow summary"
RAW=$(api GET "/transactions/cashflow-summary/?start_date=$MONTH_START&end_date=$TODAY")
parse_response "$RAW"
assert_status "Cashflow summary" 200 "$HTTP_CODE" "$BODY"

CF_INCOME=$(echo "$BODY" | jq -r '.total_income // empty')
CF_EXPENSES=$(echo "$BODY" | jq -r '.total_expenses // empty')
if [ -n "$CF_INCOME" ]; then
  green "  Income: $CF_INCOME | Expenses: $CF_EXPENSES"
fi

# ─── 12. Delete expense transaction & verify balance ────────────────────────
bold "12. Delete expense transaction"
RAW=$(api DELETE "/transactions/$EXPENSE_TX_ID/")
parse_response "$RAW"
assert_status_any "Delete transaction" "$HTTP_CODE" "$BODY" 200 204

RAW=$(api GET "/accounts/$ACCOUNT_ID/")
parse_response "$RAW"
BALANCE=$(echo "$BODY" | jq -r '.balance // empty')
# After set-balance to 5000, deleting the $120 debit adds back 120 → 5120
EXPECTED="5120.00"
if [ "$BALANCE" = "$EXPECTED" ]; then
  green "  ✓ Balance after delete: \$$BALANCE"
  PASS=$((PASS + 1))
else
  red  "  ✗ Balance after delete: got \$$BALANCE, expected \$$EXPECTED"
  FAIL=$((FAIL + 1))
fi

# ─── 13. Clean up ───────────────────────────────────────────────────────────
bold "13. Clean up"
RAW=$(api DELETE "/transactions/$INCOME_TX_ID/")
parse_response "$RAW"
assert_status_any "Delete income transaction" "$HTTP_CODE" "$BODY" 200 204

RAW=$(api DELETE "/accounts/$ACCOUNT_ID/")
parse_response "$RAW"
assert_status_any "Delete account" "$HTTP_CODE" "$BODY" 200 204

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
bold "═══════════════════════════════════"
if [ "$FAIL" -eq 0 ]; then
  green "  All $PASS checks passed"
else
  red  "  $PASS passed, $FAIL FAILED"
fi
bold "═══════════════════════════════════"

[ "$FAIL" -eq 0 ]
