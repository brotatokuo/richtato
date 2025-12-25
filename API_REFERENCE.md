# API Reference

Complete API documentation for the Richtato backend.

## Base URL

All endpoints are prefixed with `/api/v1/` (primary) or `/api/` (alternate).

## Authentication

All endpoints require authentication via session cookies. Include `credentials: 'include'` in fetch requests.

### CSRF Protection

For all mutation requests (POST, PUT, PATCH, DELETE):
1. Fetch CSRF token: `GET /api/v1/auth/csrf/`
2. Include header: `X-CSRFToken: <token>`

---

## Authentication (`/api/v1/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/csrf/` | Get CSRF token |
| POST | `/login/` | User login |
| POST | `/register/` | User registration |
| POST | `/logout/` | User logout |
| POST | `/demo-login/` | Demo user login (creates temporary user) |
| GET | `/profile/` | Get current user profile |
| PUT | `/profile/` | Update user profile |
| GET | `/get-user-id/` | Get current user ID |
| POST | `/check-username/` | Check username availability |
| POST | `/update-username/` | Update username |
| POST | `/change-password/` | Change password |
| POST | `/update-preferences/` | Update user preferences |
| DELETE | `/delete-account/` | Delete user account |

### User Preferences (`/api/v1/auth/preferences/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/preferences/` | Get user preferences |
| PUT | `/preferences/` | Update preferences |
| GET | `/preferences/field-choices/` | Get preference field options |

### Category Settings (`/api/v1/auth/category-settings/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/category-settings/` | Get user's category settings |
| PUT | `/category-settings/` | Update category settings |

---

## Transactions (`/api/v1/transactions/`)

### Transaction CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List transactions (with filters) |
| POST | `/` | Create transaction |
| GET | `/{id}/` | Get transaction details |
| PUT | `/{id}/` | Update transaction |
| PATCH | `/{id}/` | Partial update |
| DELETE | `/{id}/` | Delete transaction |

#### Query Parameters for GET `/`

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | YYYY-MM-DD | Filter by start date |
| `end_date` | YYYY-MM-DD | Filter by end date |
| `type` | debit\|credit | Filter by transaction type |
| `account_id` | number | Filter by account |
| `category_id` | number | Filter by category |
| `search` | string | Search description |

### Transaction Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/{id}/categorize/` | Assign category to transaction |
| GET | `/summary/` | Get transaction summary for date range |
| GET | `/uncategorized/` | List uncategorized transactions |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories/` | List all user categories |
| POST | `/categories/` | Create category |
| GET | `/categories/{id}/keywords/` | List category keywords |
| POST | `/categories/{id}/keywords/` | Add keyword to category |
| DELETE | `/categories/{id}/keywords/{kid}/` | Delete keyword |

### Bulk Recategorization

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recategorize/` | Start bulk recategorization |
| GET | `/recategorize/{task_id}/` | Get recategorization progress |

---

## Accounts (`/api/v1/accounts/`)

### Account CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all accounts |
| POST | `/` | Create account |
| GET | `/{id}/` | Get account details |
| PUT | `/{id}/` | Update account |
| PATCH | `/{id}/` | Partial update |
| DELETE | `/{id}/` | Delete account |

### Account Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/field-choices/` | Get account type/entity options |
| GET | `/{id}/balance-history/` | Get balance history (chart data) |
| GET | `/{id}/transactions/` | List account transactions |
| POST | `/details/` | Create balance update entry |
| GET | `/summary/` | Get accounts summary |

---

## Budgets (`/api/v1/budgets/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all budgets |
| POST | `/` | Create budget |
| GET | `/{id}/` | Get budget details |
| PUT | `/{id}/` | Update budget |
| DELETE | `/{id}/` | Delete budget |
| GET | `/{id}/progress/` | Get budget progress |
| GET | `/current/` | Get current active budget |

---

## Asset Dashboard (`/api/v1/asset-dashboard/`)

Net worth and financial overview endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics/` | Key financial metrics (net worth, income, expenses) |
| GET | `/networth-history/` | Net worth trend data for charts |
| GET | `/account-breakdown/` | Breakdown by account type |
| GET | `/income-expenses/` | Income vs expenses comparison |
| GET | `/cash-flow/` | Cash flow data |
| GET | `/savings/` | Savings rate data |
| GET | `/top-categories/` | Top spending categories |
| GET | `/sankey-data/` | Sankey diagram flow data |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | YYYY-MM-DD | Period start |
| `end_date` | YYYY-MM-DD | Period end |
| `period` | string | Predefined period (e.g., "month", "year") |

---

## Budget Dashboard (`/api/v1/budget-dashboard/`)

Budget tracking and analytics endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/progress/` | Budget vs actual spending |
| GET | `/progress/multi-month/` | Multi-month budget progress |
| GET | `/expense-categories/` | Expenses grouped by category |
| GET | `/rankings/` | Category spending rankings |
| GET | `/expense-years/` | Available years with expense data |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | number | Year (e.g., 2025) |
| `month` | number | Month (1-12) |
| `start_date` | YYYY-MM-DD | Custom period start |
| `end_date` | YYYY-MM-DD | Custom period end |

---

## Bank Sync (`/api/v1/sync/`)

Bank connection and transaction sync endpoints (Plaid integration).

### Connections

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/connections/` | List bank connections |
| POST | `/connections/` | Create connection |
| GET | `/connections/{id}/` | Get connection details |
| DELETE | `/connections/{id}/` | Disconnect bank |
| POST | `/connections/{id}/sync/` | Trigger transaction sync |
| GET | `/connections/{id}/jobs/` | List sync jobs |
| GET | `/connections/{id}/progress/` | Get current sync progress |

### Plaid Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/plaid/link-token/` | Create Plaid Link token |
| POST | `/plaid/exchange-token/` | Exchange public token for access token |

---

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### List Response

```json
{
  "transactions": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 25
}
```

### Error Response

```json
{
  "error": "Error message",
  "details": { ... }
}
```

---

## Data Models

### Transaction

```typescript
{
  id: number;
  account: number;
  account_name: string;
  date: string;           // YYYY-MM-DD
  amount: number;
  signed_amount: number;  // Negative for debits
  description: string;
  transaction_type: 'debit' | 'credit';
  category: number | null;
  category_name: string | null;
  category_type: 'income' | 'expense' | 'transfer' | 'investment' | 'other';
  status: string;
  sync_source: string;
  categorization_status: string;
}
```

### Account

```typescript
{
  id: number;
  name: string;
  account_type: string;
  institution_name: string;
  current_balance: number;
  is_active: boolean;
  sync_source: string;
  has_connection: boolean;
  last_sync: string | null;
}
```

### Category

```typescript
{
  id: number;
  name: string;
  slug: string;
  parent: number | null;
  type: 'income' | 'expense' | 'transfer' | 'investment' | 'other';
  icon: string;
  color: string;
}
```

### Budget

```typescript
{
  id: number;
  name: string;
  period_type: 'monthly' | 'yearly';
  start_date: string;
  is_active: boolean;
  allocations: { [category_id: string]: number };
}
```
