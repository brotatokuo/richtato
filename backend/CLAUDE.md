# Backend Documentation

This file provides guidance when working with the Richtato backend codebase.

## Project Overview

Richtato Backend is a **Django REST Framework API** for an AI-native personal finance platform. It handles transaction ingestion, AI-powered categorization, budget analytics, bank sync (Teller + Plaid), and net worth tracking. The backend is designed to be fast, reliable, and extensible — the AI layer should feel like a natural part of every user workflow.

## Tech Stack

- **Django 5.x** with Django REST Framework
- **PostgreSQL** database
- **Gunicorn** WSGI server
- **Loguru** for structured logging
- **OpenAI API** for AI categorization and insights
- **Plaid** for bank sync (exchange token flow)
- **Teller** for bank sync (certificate-based)

## Development Commands

```bash
# Docker development
docker compose up -d
docker compose logs -f backend
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py migrate
docker compose restart backend

# Direct development
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser
python manage.py shell

# Reset demo data
./create_or_reset_demo.sh
```

## Architecture Pattern

### Repository → Service → View

```
Views (HTTP) → Services (Business Logic) → Repositories (Data Access)
```

Each Django app follows this structure:

```
apps/{app_name}/
├── views.py                      # API endpoints (thin, delegates to services)
├── services/
│   └── {name}_service.py         # Business logic, calculations, orchestration
├── repositories/
│   └── {name}_repository.py      # Database queries only — no business logic
├── models.py                     # Django ORM models
├── serializers.py                # DRF serializers
├── urls.py                       # URL routing
└── tests.py                      # Unit tests
```

**Example flow** (creating a transaction):
1. `views.py`: Receives HTTP POST, validates with serializer
2. `transaction_service.py`: Applies business rules, triggers auto-categorization
3. `transaction_repository.py`: Executes `Transaction.objects.create()`

## Django Apps

| App | Purpose |
|-----|---------|
| `transaction` | Core transactions, categories, bulk operations |
| `financial_account` | Bank accounts, credit cards, investment accounts |
| `budget` | Budget creation and allocation |
| `budget_dashboard` | Budget analytics, category breakdowns, trends |
| `asset_dashboard` | Net worth, income/expense metrics, account history |
| `sync` | Bank sync orchestration (Plaid + Teller) |
| `categorization` | AI categorization, keyword rules, categorization history |
| `richtato_user` | User model, auth, preferences, demo user |
| `core` | Shared utilities, middleware, base classes |

## Core Models

### User (`richtato_user.User`)
Extended Django user with preferences (currency, date format, display settings).

### FinancialAccount (`financial_account.FinancialAccount`)
```python
- user: FK(User)
- name: str
- account_type: str          # 'checking', 'savings', 'credit', 'investment'
- institution: FK(FinancialInstitution)
- current_balance: Decimal
- is_liability: bool          # True for credit/loan accounts (subtract from net worth)
```

### Transaction (`transaction.Transaction`)
```python
- user: FK(User)
- account: FK(FinancialAccount)
- category: FK(TransactionCategory, null=True)
- amount: Decimal
- transaction_type: str       # 'debit' or 'credit'
- date: Date
- description: str
- merchant_name: str
- external_id: str            # Plaid/Teller transaction ID (dedup key)
- notes: str
```

### TransactionCategory (`transaction.TransactionCategory`)
```python
- user: FK(User)
- parent: FK(self, null=True) # Hierarchical: parent=None means top-level
- name: str
- slug: str
- type: str                   # 'income', 'expense', 'transfer', 'investment'
- icon: str                   # Lucide icon name
- color: str                  # Hex or CSS color
```

### Budget (`budget.Budget`)
```python
- user: FK(User)
- name: str
- period_type: str            # 'monthly', 'yearly'
- start_date: Date
- is_active: bool
- allocations: JSON           # {category_id: amount}
```

### BankConnection (`sync.BankConnection`)
```python
- user: FK(User)
- provider: str               # 'plaid' or 'teller'
- institution_name: str
- access_token: str           # Encrypted
- last_synced: DateTime
```

## API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /login/` — User login
- `POST /logout/` — User logout
- `GET /me/` — Current user info
- `GET /demo-login/` — Demo user access (auto-creates populated demo account)

### Transactions (`/api/v1/transactions/`)
- `GET /` — List transactions (filters: `date_from`, `date_to`, `category`, `account`, `search`)
- `POST /` — Create transaction
- `GET /{id}/` — Get transaction detail
- `PUT /{id}/` — Update transaction
- `DELETE /{id}/` — Delete transaction
- `GET /categories/` — List all user categories (hierarchical)
- `POST /categories/` — Create category
- `PUT /categories/{id}/` — Update category
- `DELETE /categories/{id}/` — Delete category
- `POST /recategorize/` — **AI bulk recategorization** (queues OpenAI calls for selected transactions)

### Accounts (`/api/v1/accounts/`)
- `GET /` — List accounts with balances
- `POST /` — Create manual account
- `PUT /{id}/` — Update account
- `DELETE /{id}/` — Delete account
- `POST /{id}/balance/` — Update manual account balance

### Budgets (`/api/v1/budgets/`)
- `GET /` — List budgets
- `POST /` — Create budget
- `PUT /{id}/` — Update budget allocations
- `GET /progress/` — Budget vs actual spending by period

### Dashboards
- `GET /api/v1/asset-dashboard/metrics/` — Net worth, total assets, liabilities, income, expenses
- `GET /api/v1/asset-dashboard/trends/` — Historical net worth and balance trends
- `GET /api/v1/budget-dashboard/metrics/` — Budget utilization and variance
- `GET /api/v1/budget-dashboard/category-breakdown/` — Spending by category for period

### Bank Sync (`/api/v1/sync/`)
- `POST /plaid/link-token/` — Get Plaid Link token to initiate connection
- `POST /plaid/exchange-token/` — Exchange public token, create BankConnection
- `POST /teller/enroll/` — Initiate Teller enrollment
- `POST /teller/exchange-token/` — Complete Teller enrollment, create BankConnection
- `GET /connections/` — List all bank connections with sync status
- `POST /connections/{id}/sync/` — Trigger transaction sync for a connection
- `DELETE /connections/{id}/` — Disconnect bank account
- `GET /status/` — Current sync status (polled by frontend for real-time feedback)

### User (`/api/v1/user/`)
- `GET /profile/` — User profile and preferences
- `PUT /profile/` — Update preferences
- `GET /category-settings/` — Category keyword rules
- `POST /category-settings/` — Add keyword rule

## Key Files

| File | Purpose |
|------|---------|
| `richtato/settings.py` | Django configuration |
| `richtato/urls.py` | Root URL routing |
| `config/categories_defaults.yaml` | Default category hierarchy seeded for new users |
| `integrations/plaid/client.py` | Plaid API client wrapper |
| `integrations/teller/client.py` | Teller API client wrapper |
| `artificial_intelligence/ai.py` | OpenAI categorization engine |

## AI Categorization

The AI layer (`artificial_intelligence/ai.py`) uses OpenAI to categorize transactions:

- **Input**: Transaction description + merchant name + amount
- **Context**: User's full category list (name, type, keywords)
- **Output**: Predicted category slug + confidence
- **Caching**: Results cached by `(description, merchant, user_category_set_hash)` to minimize API calls
- **Bulk recategorize**: Frontend triggers `POST /transactions/recategorize/` which queues async categorization for selected transactions and streams progress via polling

**When adding AI features**: Follow the existing pattern in `ai.py` — pass structured user context, return typed results, always cache aggressively.

## Bank Sync Architecture

Both Plaid and Teller follow the same pattern:

1. **Initiate**: Frontend calls link-token endpoint → opens bank's OAuth/UI
2. **Exchange**: Frontend sends public token → backend exchanges for access token, stores encrypted in `BankConnection`
3. **Sync**: Background process fetches transactions → deduplicates by `external_id` → runs auto-categorization → updates account balances
4. **Status**: `GET /sync/status/` polled by frontend every few seconds during active sync

**Deduplication**: `external_id` (Plaid/Teller transaction ID) is the unique key. Syncing is idempotent — re-syncing never creates duplicates.

## Conventions

### Logging
```python
from loguru import logger

logger.info("Processing transaction", transaction_id=tx.id, user_id=user.id)
logger.error("Sync failed", provider="plaid", error=str(e))
logger.exception("Unexpected error in categorization")  # includes traceback
```

### Error Handling in Views
```python
from rest_framework.response import Response
from rest_framework import status

try:
    result = service.do_something()
    return Response(result, status=status.HTTP_200_OK)
except ValidationError as e:
    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
except Exception as e:
    logger.exception("Unexpected error")
    return Response({"error": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Repository Pattern
```python
# repositories/transaction_repository.py
class TransactionRepository:
    def get_by_user(self, user: User, filters: dict) -> QuerySet[Transaction]:
        qs = Transaction.objects.filter(user=user)
        if filters.get('date_from'):
            qs = qs.filter(date__gte=filters['date_from'])
        return qs.select_related('category', 'account')

    def create(self, **kwargs) -> Transaction:
        return Transaction.objects.create(**kwargs)

    def bulk_update_category(self, ids: list[int], category) -> int:
        return Transaction.objects.filter(id__in=ids).update(category=category)
```

### Service Pattern
```python
# services/transaction_service.py
class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()
        self.categorization = CategorizationService()

    def create_transaction(self, user: User, data: dict) -> Transaction:
        transaction = self.repository.create(user=user, **data)
        self.categorization.auto_categorize(transaction)
        return transaction

    def bulk_recategorize(self, user: User, transaction_ids: list[int]) -> dict:
        transactions = self.repository.get_by_ids(user, transaction_ids)
        results = self.categorization.recategorize_batch(transactions)
        return {"updated": len(results), "categories": results}
```

## Integrations

### Plaid (`integrations/plaid/`)
- Exchange token flow via Link
- Pulls accounts and transactions
- Webhooks for real-time updates (optional)

### Teller (`integrations/teller/`)
- Certificate-based enrollment
- Direct bank API access (no intermediary fees)
- Preferred over Plaid where available

### OpenAI (`artificial_intelligence/ai.py`)
- GPT-4o-mini for cost-effective categorization at scale
- System prompt includes user's full category hierarchy
- Few-shot examples from user's past categorization choices (personalization)
- Batch API calls to reduce latency and cost

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.transaction
python manage.py test apps.budget_dashboard

# With coverage
coverage run manage.py test
coverage report
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `PLAID_CLIENT_ID` | Plaid client ID |
| `PLAID_SECRET` | Plaid secret key |
| `PLAID_ENV` | `sandbox`, `development`, or `production` |
| `TELLER_CERT_PATH` | Path to Teller TLS certificate |
| `TELLER_KEY_PATH` | Path to Teller private key |
| `OPENAI_API_KEY` | OpenAI API key for AI categorization |
| `ALLOWED_HOSTS` | Django allowed hosts |
| `CORS_ORIGINS` | Allowed CORS origins |
