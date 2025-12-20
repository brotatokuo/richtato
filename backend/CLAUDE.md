# Backend Documentation

This file provides guidance when working with the Richtato backend codebase.

## Project Overview

Richtato Backend is a **Django REST Framework API** for personal finance management. It handles transaction tracking, budget management, bank account syncing (Teller/Plaid), and AI-powered categorization.

## Tech Stack

- **Django 5.x** with Django REST Framework
- **PostgreSQL** database
- **Gunicorn** WSGI server
- **Loguru** for logging
- **OpenAI API** for AI categorization
- **Teller/Plaid** for bank sync integrations

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
├── views.py          # API endpoints (thin, delegates to services)
├── services/
│   └── {name}_service.py    # Business logic, calculations
├── repositories/
│   └── {name}_repository.py # Database queries only
├── models.py         # Django ORM models
├── serializers.py    # DRF serializers
├── urls.py           # URL routing
└── tests.py          # Unit tests
```

**Example flow** (creating a transaction):
1. `views.py`: Receives HTTP POST, validates with serializer
2. `transaction_service.py`: Applies business rules, triggers categorization
3. `transaction_repository.py`: Executes `Transaction.objects.create()`

## Django Apps

| App | Purpose |
|-----|---------|
| `transaction` | Core transactions and categories |
| `financial_account` | Bank accounts, credit cards, investments |
| `budget` | Budget creation and allocation |
| `budget_dashboard` | Budget analytics and trends |
| `asset_dashboard` | Net worth, income/expense metrics |
| `sync` | Bank sync (Teller, Plaid integration) |
| `categorization` | AI categorization, keywords, history |
| `richtato_user` | User model, auth, demo user |
| `core` | Shared utilities, middleware |

## Core Models

### User (`richtato_user.User`)
Extended Django user with preferences.

### FinancialAccount (`financial_account.FinancialAccount`)
```python
- user: FK(User)
- name: str
- account_type: str  # 'checking', 'savings', 'credit', 'investment'
- institution: FK(FinancialInstitution)
- current_balance: Decimal
- is_liability: bool  # True for credit cards
```

### Transaction (`transaction.Transaction`)
```python
- user: FK(User)
- account: FK(FinancialAccount)
- category: FK(TransactionCategory, null=True)
- amount: Decimal
- transaction_type: str  # 'debit' or 'credit'
- date: Date
- description: str
- merchant_name: str
- external_id: str  # Teller/Plaid ID
```

### TransactionCategory (`transaction.TransactionCategory`)
```python
- user: FK(User)
- parent: FK(self, null=True)  # Hierarchical categories
- name: str
- slug: str
- type: str  # 'income', 'expense', 'transfer', 'investment'
- icon: str
- color: str
```

### Budget (`budget.Budget`)
```python
- user: FK(User)
- name: str
- period_type: str  # 'monthly', 'yearly'
- start_date: Date
- is_active: bool
- allocations: JSON  # {category_id: amount}
```

### BankConnection (`sync.BankConnection`)
```python
- user: FK(User)
- provider: str  # 'teller' or 'plaid'
- institution_name: str
- access_token: str (encrypted)
- last_synced: DateTime
```

## API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /login/` - User login
- `POST /logout/` - User logout
- `GET /me/` - Current user info
- `GET /demo-login/` - Demo user access

### Transactions (`/api/v1/transactions/`)
- `GET /` - List transactions (filters: date, category, account)
- `POST /` - Create transaction
- `GET /{id}/` - Get transaction
- `PUT /{id}/` - Update transaction
- `DELETE /{id}/` - Delete transaction
- `GET /categories/` - List categories
- `POST /categories/` - Create category
- `POST /recategorize/` - AI bulk recategorization

### Accounts (`/api/v1/accounts/`)
- `GET /` - List accounts
- `POST /` - Create account
- `PUT /{id}/` - Update account
- `DELETE /{id}/` - Delete account
- `POST /{id}/balance/` - Update balance

### Budgets (`/api/v1/budgets/`)
- `GET /` - List budgets
- `POST /` - Create budget
- `PUT /{id}/` - Update budget
- `GET /progress/` - Budget progress by period

### Dashboards
- `GET /api/v1/asset-dashboard/metrics/` - Net worth, income, expenses
- `GET /api/v1/asset-dashboard/trends/` - Historical trends
- `GET /api/v1/budget-dashboard/metrics/` - Budget vs actual
- `GET /api/v1/budget-dashboard/category-breakdown/` - Spending by category

### Bank Sync (`/api/v1/teller/`)
- `POST /connect/` - Initialize bank connection
- `POST /sync/` - Trigger transaction sync
- `GET /connections/` - List bank connections
- `DELETE /connections/{id}/` - Disconnect bank

## Key Files

| File | Purpose |
|------|---------|
| `richtato/settings.py` | Django configuration |
| `richtato/urls.py` | Root URL routing |
| `config/categories_defaults.yaml` | Default category definitions |
| `integrations/teller/client.py` | Teller API client |
| `integrations/plaid/client.py` | Plaid API client |
| `artificial_intelligence/ai.py` | OpenAI categorization |

## Conventions

### Logging
```python
from loguru import logger

logger.info("Processing transaction", transaction_id=tx.id)
logger.error("Failed to sync", error=str(e))
```

### Error Handling
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
    def get_by_user(self, user: User) -> QuerySet[Transaction]:
        return Transaction.objects.filter(user=user)

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return Transaction.objects.filter(id=transaction_id).first()

    def create(self, **kwargs) -> Transaction:
        return Transaction.objects.create(**kwargs)
```

### Service Pattern
```python
# services/transaction_service.py
class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()
        self.categorization = CategorizationService()

    def create_transaction(self, user: User, data: dict) -> Transaction:
        # Business logic here
        transaction = self.repository.create(user=user, **data)
        self.categorization.auto_categorize(transaction)
        return transaction
```

## Integrations

### Teller (`integrations/teller/`)
- Syncs bank accounts and transactions
- OAuth-based connection flow
- Webhook support for real-time updates

### Plaid (`integrations/plaid/`)
- Alternative to Teller
- Link token flow for connection

### OpenAI (`artificial_intelligence/ai.py`)
- GPT-based transaction categorization
- Uses user's category list for context
- Caches results to reduce API calls

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.transaction

# With coverage
coverage run manage.py test
coverage report
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection |
| `TELLER_API_KEY` | Teller API credentials |
| `PLAID_CLIENT_ID` | Plaid client ID |
| `PLAID_SECRET` | Plaid secret |
| `OPENAI_API_KEY` | OpenAI API key |
