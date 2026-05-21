# Backend Guide

This file documents the current Richtato backend patterns for agents and developers.

## Overview

The backend is a Django 5.x and Django REST Framework API for personal finance data, budgets, dashboards, household sharing, Plaid sync, and AI categorization.

## Stack

- Django 5.x and Django REST Framework.
- PostgreSQL in deployed/local Docker environments.
- SQLite test settings for the default pytest path.
- Gunicorn for production serving.
- Loguru for logging.
- Plaid for bank sync.
- OpenAI for AI categorization.

## Commands

Docker:

```bash
docker compose up -d
docker compose logs -f backend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell
docker compose restart backend
```

Direct backend development:

```bash
python manage.py runserver
python manage.py migrate
python manage.py shell
./create_or_reset_demo.sh
```

Validation from `backend/`:

```bash
ruff check .
ruff format --check .
python manage.py makemigrations --check --dry-run --skip-checks --settings=richtato.settings
python manage.py check --settings=richtato.test_settings
python -m pytest apps/ -v --tb=short
```

## App Structure

```text
backend/
├── apps/
│   ├── transaction/
│   ├── financial_account/
│   ├── budget/
│   ├── budget_dashboard/
│   ├── asset_dashboard/
│   ├── sync/
│   ├── categorization/
│   ├── household/
│   ├── richtato_user/
│   └── core/
├── artificial_intelligence/
├── integrations/
│   └── plaid/
├── statement_imports/
├── config/
└── richtato/
```

Typical app layout:

```text
apps/{app}/
├── views.py
├── services/
├── repositories/
├── models.py
├── serializers.py
├── urls.py
└── tests/
```

Some apps are simpler or older and do not fully follow this layout. Match the local pattern unless the change clearly benefits from extracting a service or repository.

## Architecture Pattern

Use Repository -> Service -> View for new backend work.

- Views handle HTTP, authentication, serializers, and response status codes.
- Services own business logic, orchestration, calculations, and cross-app coordination.
- Repositories own ORM queries, persistence, and `select_related`/`prefetch_related` choices.

CRUD APIs usually use DRF `APIView` classes. Dashboard endpoints often use `@login_required` function views returning `JsonResponse` with repository/service dependency injection.

Service errors commonly use `ValueError` for domain issues. Views should catch expected service errors and return `400` or `404`; unexpected errors should use `logger.exception`.

## Core Models

- `richtato_user.User`: Django user extension and preferences.
- `financial_account.FinancialAccount`: accounts with `balance`, account type, liability behavior, institution, and household sharing flags.
- `transaction.Transaction`: all imported and manual transactions.
- `transaction.TransactionCategory`: hierarchical income, expense, transfer, and investment categories with soft delete support.
- `transaction.CategoryKeyword`: keyword rules for categorization.
- `budget.Budget`: budget period and household flag.
- `budget.BudgetCategory`: per-category budget amounts.
- `sync.SyncConnection`: external source connection, currently Plaid/manual.
- `sync.SyncJob`: sync run tracking.
- `sync.UserSyncStatus`: frontend polling state.
- `household.Household`: household membership for shared finance views.

## URLs

Most APIs are mounted under both `/api/...` and `/api/v1/...` in `richtato/urls.py`.

Important roots:

- `/api/v1/auth/`
- `/api/v1/accounts/`
- `/api/v1/card-accounts/`
- `/api/v1/transactions/`
- `/api/v1/budgets/`
- `/api/v1/asset-dashboard/`
- `/api/v1/budget-dashboard/`
- `/api/v1/sync/`
- `/api/v1/household/`

API docs are exposed at `/api/docs/` and Redoc at `/redoc/` when the backend is running.

## Household Scope

Household-aware list and aggregate endpoints should use `apps.household.scope.get_scope_user_ids(request)`.

Pattern:

- Personal scope uses the request user only.
- Household scope includes household member user IDs.
- Shared data should be constrained to accounts marked `shared_with_household=True`.
- Household budgets use `Budget.is_household=True`.
- Frontend sends `scope=household` only for household scope; personal scope omits the parameter.

Use existing household tests, especially `apps/household/tests/test_scope.py`, as references.

## Transactions And Balances

`apps.transaction.signals` updates account balances and balance history on transaction save/delete. Do not manually adjust `FinancialAccount.balance` around normal transaction CRUD unless you are deliberately bypassing or testing signal behavior.

Use `TransactionService` for manual transaction flows so categorization and side effects stay consistent. Tests that create transactions directly should account for signal side effects.

## Budget And Dashboard Aggregation

- Use `apps.core.constants` filters for expense, income, transfer, and investment classification.
- Avoid reimplementing category-type logic in dashboard repositories.
- Dashboard services should perform calculations; repositories should perform queries.
- Budget uses `Budget` and `BudgetCategory` rows, not JSON allocation blobs.

## Sync And Integrations

CSV/Excel statement import is the primary no-aggregator ingestion path for new bank data work.

- `apps/financial_account/services/statement_import_service.py` parses CSV/XLS/XLSX statements through institution adapters.
- `apps/financial_account/services/statement_file_service.py` stores original statement files locally under `local_data/statements/<user>/<account>/<year>/<month>/` and reuses the import service for preview/commit.
- Statement imports should preview before commit and classify rows as new, duplicate, invalid, or possible changed.
- Deduplication is row-level so current/open statements can overlap later closed statements.
- Current/open statement exports are provisional; closed statements are authoritative and should flag changed provisional rows for review.
- `integrations/base.py` defines normalized banking client behavior.
- `integrations/plaid/client.py` implements Plaid client behavior.
- `apps/sync/services/` contains legacy sync orchestration and Plaid-specific logic.
- Plaid code may remain for existing data, but avoid making paid aggregators the default product path for new import features.

Do not document or add Teller code paths unless the task is explicitly to implement Teller.

## AI Categorization

- `artificial_intelligence/ai.py` contains the low-level OpenAI integration.
- `apps/categorization/services/ai_categorization_service.py` wraps app-level categorization behavior.
- Batch work uses categorization services, queue models, and management commands.

Keep AI prompts structured and pass enough category context for reliable classification. Persist history where the existing service expects it.

## Serializers

Use serializers at the view boundary. Prefer separate read and write serializers when create/update payloads differ from model output. Services should receive validated data rather than raw request data.

## Logging

Use Loguru:

```python
from loguru import logger

logger.info("Sync started", user_id=user.id, connection_id=connection.id)
logger.exception("Unexpected sync failure")
```

Avoid `print` and stdlib `logging` in app code.

## Testing

Default tests use pytest with `DJANGO_SETTINGS_MODULE=richtato.test_settings` from `backend/conftest.py` and `pyproject.toml`.

```bash
python -m pytest apps/ -v --tb=short
```

Test classes use `Test*`; test files use `test_*.py` or `*_test.py`. Per-app `tests/` directories are preferred, though some legacy `tests.py` files remain.

Use factories/fixtures already present in app test directories when possible. For transaction tests, remember signal side effects on account balances.

## Migrations

Use normal Django migrations for model changes:

```bash
python manage.py makemigrations
python manage.py migrate
```

Before committing backend changes, verify no missing migrations:

```bash
python manage.py makemigrations --check --dry-run --skip-checks --settings=richtato.settings
```
