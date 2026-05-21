# API Reference

This is the maintained HTTP API reference for Richtato. When the backend is running, verify endpoint drift against Swagger at `/api/docs/` or Redoc at `/redoc/`.

## Base URL

Primary frontend-compatible routes are under `/api/v1/`. Many endpoints are also mounted under `/api/` for compatibility.

Authentication uses Django session cookies. Frontend requests should include credentials. Mutation requests require CSRF protection.

```typescript
fetch('/api/v1/auth/profile/', { credentials: 'include' });
```

For POST, PUT, PATCH, and DELETE:

1. Fetch `GET /api/v1/auth/csrf/`.
2. Send `X-CSRFToken: <token>`.

## Shared Query Parameters

Many list and dashboard endpoints support household scope:

| Parameter | Values | Description |
| --- | --- | --- |
| `scope` | `household` | Include household-visible data. Omit for personal scope. |

Do not send `scope=personal`; personal scope is the default.

Common date filters:

| Parameter | Format | Description |
| --- | --- | --- |
| `start_date` | `YYYY-MM-DD` | Inclusive start date |
| `end_date` | `YYYY-MM-DD` | Inclusive end date |
| `year` | number | Calendar year |
| `month` | number | Month number, 1-12 |

## Authentication And User (`/api/v1/auth/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/csrf/` | Get CSRF token |
| `POST` | `/login/` | Log in |
| `POST` | `/register/` | Register |
| `POST` | `/logout/` | Log out |
| `POST` | `/demo-login/` | Log in as demo user |
| `GET` | `/profile/` | Get profile |
| `PUT` | `/profile/` | Update profile |
| `GET` | `/get-user-id/` | Get current user ID |
| `POST` | `/check-username/` | Check username availability |
| `POST` | `/update-username/` | Update username |
| `POST` | `/change-password/` | Change password |
| `POST` | `/update-preferences/` | Update preferences |
| `DELETE` | `/delete-account/` | Delete account |
| `GET` | `/categories/` | Get user categories |
| `GET` | `/category-settings/` | Get category settings |
| `PUT` | `/category-settings/` | Update category settings |
| `GET` | `/preferences/` | Get preferences |
| `PUT` | `/preferences/` | Update preferences |
| `GET` | `/preferences/field-choices/` | Get preference field choices |

## Accounts (`/api/v1/accounts/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | List accounts |
| `POST` | `/` | Create account |
| `GET` | `/field-choices/` | Get account type/entity choices |
| `GET` | `/{id}/` | Get account |
| `PUT/PATCH` | `/{id}/` | Update account |
| `DELETE` | `/{id}/` | Delete account |
| `GET` | `/{id}/balance-history/` | Get balance history |
| `GET` | `/{id}/transactions/` | List account transactions |
| `GET` | `/summary/` | Get account summary |
| `POST` | `/details/` | Add balance update entry |
| `POST` | `/import-csv/` | Import statement CSV |
| `GET` | `/import-statement/` | List supported CSV/Excel statement institutions |
| `POST` | `/import-statement/` | Preview or commit CSV/Excel statement import |
| `GET` | `/statements/` | List locally stored statement files and account/year/month tree |
| `POST` | `/statements/` | Upload a statement file into local account/year/month storage |
| `GET` | `/statements/{id}/` | Get statement file metadata |
| `PATCH` | `/statements/{id}/` | Update statement metadata and move folders if account/period changes |
| `DELETE` | `/statements/{id}/` | Soft-delete statement file metadata |
| `GET` | `/statements/{id}/download/` | Download the stored original statement file |
| `POST` | `/statements/{id}/preview/` | Preview import from the stored statement file |
| `POST` | `/statements/{id}/import/` | Commit import from the stored statement file |

Household-aware account reads may accept `scope=household`.

Card-specific account routes are mounted at `/api/v1/card-accounts/`.

### Statement Imports

`POST /api/v1/accounts/import-statement/` accepts multipart form data:

- `file`: CSV, XLS, or XLSX statement export.
- `account`: target account ID.
- `institution`: one of `bofa`, `marcus`, `amex`, `robinhood_bank`, `fidelity`, `robinhood_investments`, `guideline`, or `chase`.
- `mode`: `preview` or `commit`.
- `statement_status`: `provisional` for current/open exports or `closed` for final statements.
- `statement_period`: optional label such as `2025-06`.

Statement imports use row-level deduplication. Current/open statement exports are provisional and may overlap later closed statements; duplicates are skipped and changed provisional rows are flagged for review.

Statement files uploaded through `/statements/` are stored locally under `local_data/statements/<user_id>/<account_id>/<year>/<month>/`. The database stores metadata, file hash, account, institution, period, status, and the latest preview/import summary.

## Transactions (`/api/v1/transactions/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | List transactions |
| `POST` | `/` | Create transaction |
| `GET` | `/filter-options/` | Get filter options |
| `GET` | `/{id}/` | Get transaction |
| `PUT/PATCH` | `/{id}/` | Update transaction |
| `DELETE` | `/{id}/` | Delete transaction |
| `POST` | `/{id}/categorize/` | Assign category |
| `GET` | `/summary/` | Get transaction summary |
| `GET` | `/cashflow-summary/` | Get cashflow summary |
| `GET` | `/uncategorized/` | List uncategorized transactions |

List query parameters include date range, category, account, type, search, pagination, and optional `scope=household`.

### Categories

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/categories/` | List categories |
| `POST` | `/categories/` | Create category |
| `GET` | `/categories/{id}/` | Get category |
| `PUT/PATCH` | `/categories/{id}/` | Update category |
| `DELETE` | `/categories/{id}/` | Soft-delete category |
| `GET` | `/categories/{id}/keywords/` | List keywords |
| `POST` | `/categories/{id}/keywords/` | Add keyword |
| `DELETE` | `/categories/{id}/keywords/{keyword_id}/` | Delete keyword |

### Recategorization

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/recategorize/` | Start AI recategorization |
| `GET` | `/recategorize/{task_id}/` | Get recategorization progress |

## Budgets (`/api/v1/budgets/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | List budgets |
| `POST` | `/` | Create budget |
| `GET` | `/{id}/` | Get budget |
| `PUT/PATCH` | `/{id}/` | Update budget |
| `DELETE` | `/{id}/` | Delete budget |
| `GET` | `/{id}/progress/` | Get budget progress |
| `GET` | `/current/` | Get current budget |

Budget reads may accept `scope=household`. Household budgets use backend `Budget.is_household`.

## Asset Dashboard (`/api/v1/asset-dashboard/`)

Net worth, income, expense, savings, and account breakdown data.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/metrics/` | Key dashboard metrics |
| `GET` | `/networth-history/` | Net worth history |
| `GET` | `/account-breakdown/` | Breakdown by account type/group |
| `GET` | `/income-expenses/` | Income versus expenses |
| `GET` | `/cash-flow/` | Cash flow data |
| `GET` | `/savings/` | Savings data |
| `GET` | `/top-categories/` | Top spending categories |
| `GET` | `/sankey-data/` | Sankey flow data |

Common query parameters: `start_date`, `end_date`, `period`, and optional `scope=household`.

## Budget Dashboard (`/api/v1/budget-dashboard/`)

Budget analytics and spending breakdown data.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/progress/` | Budget progress |
| `GET` | `/progress/multi-month/` | Multi-month progress |
| `GET` | `/expense-categories/` | Expenses grouped by category |
| `GET` | `/rankings/` | Category spending rankings |
| `GET` | `/expense-years/` | Years with expense data |
| `GET` | `/annual-analysis/` | Annual spending analysis |
| `GET` | `/annual-analysis/years/` | Years available for annual analysis |

Common query parameters: `year`, `month`, `start_date`, `end_date`, and optional `scope=household`.

## Sync (`/api/v1/sync/`)

Sync is currently Plaid/manual through `SyncConnection`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/connections/` | List sync connections |
| `POST` | `/connections/` | Create sync connection |
| `GET` | `/connections/{id}/` | Get sync connection |
| `PUT/PATCH` | `/connections/{id}/` | Update sync connection |
| `DELETE` | `/connections/{id}/` | Disconnect |
| `POST` | `/connections/{id}/sync/` | Trigger sync |
| `GET` | `/connections/{id}/jobs/` | List jobs for connection |
| `GET` | `/connections/{id}/progress/` | Get active job progress |
| `POST` | `/plaid/link-token/` | Create Plaid Link token |
| `POST` | `/plaid/exchange-token/` | Exchange Plaid public token |
| `GET` | `/status/` | Get user sync status |
| `GET` | `/jobs/` | Get user sync job history |

Cron sync is mounted separately at `/api/cron/sync/`.

## Household (`/api/v1/household/`)

Household endpoints are v1-only.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Get household state |
| `POST` | `/` | Create household |
| `POST` | `/invite/` | Create invite |
| `POST` | `/join/` | Join household |
| `POST` | `/leave/` | Leave household |
| `GET` | `/members/` | List household members |

Household scope for financial data is not controlled by these endpoints directly. Use `scope=household` on supported account, transaction, budget, and dashboard reads.

## Response Shape Conventions

Successful list and detail responses usually return JSON objects or arrays shaped by serializers. Validation errors return `400` responses with error details. Authentication failures return `401` or `403` depending on session and CSRF state.

Frontend API services should centralize response handling in `frontend/src/lib/api/` rather than parsing errors ad hoc in components.
