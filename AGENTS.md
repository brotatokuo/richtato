# Agent Guide

Use this file as the starting point for AI-agent work in Richtato. Keep it concise and update the deeper docs when behavior or architecture changes.

## What This Repo Is

Richtato is an AI-native personal finance app for spending, budgets, net worth, statement uploads, household sharing, and AI categorization. The UX target is Monarch Money: clear financial data, low-friction transaction workflows, polished responsive layouts, and dark/light parity.

## Read This First

| Work area | Read |
| --- | --- |
| Frontend changes | `frontend/CLAUDE.md`, `.cursor/rules/frontend-patterns.mdc`, `.cursor/rules/route-registration.mdc` |
| Backend changes | `backend/CLAUDE.md`, `.cursor/rules/backend-patterns.mdc` |
| API contracts | `API_REFERENCE.md`, then Swagger at `/api/docs/` when the backend is running |
| Validation before commit | `.cursor/rules/pre-commit-checks.mdc` |
| Product and UI defaults | `.cursorrules`, `.cursor/rules/product-conventions.mdc` |

## Current Source Of Truth

- Frontend routing: `frontend/src/App.tsx`.
- Desktop navigation: `frontend/src/components/Sidebar.tsx`.
- Mobile navigation: `frontend/src/components/BottomTabBar.tsx` and `frontend/src/pages/More.tsx`.
- Header titles/icons: `frontend/src/components/Layout.tsx`.
- Backend URL roots: `backend/richtato/urls.py`.
- Household scope helper: `backend/apps/household/scope.py`.
- Statement imports: `backend/apps/financial_account/services/statement_import_service.py`.
- Statement file library: `backend/apps/financial_account/services/statement_file_service.py`.
- Transaction balance side effects: `backend/apps/transaction/signals.py`.
- Frontend API services: `frontend/src/lib/api/`.

## Known Pitfalls

- The active dashboard route is `/dashboard`, not `/report`.
- The transaction page route is `/transactions`, not `/data`.
- The Vite dev server runs on port `3000`.
- Budgets use `/api/v1/budgets/`, not `/api/v1/budget/`.
- User profile, preferences, and category settings live under `/api/v1/auth/`.
- Manual statement uploads with Google Drive statement storage are the primary no-aggregator ingestion path. There is no automated bank sync or Playwright agent; transactions arrive via statement uploads or manual entry.
- The full app stack is Docker-only (`db`, `backend`, `frontend`).
- Do not document Plaid, Teller, or other paid aggregators as active unless you implement them.
- Statement imports must be row-level idempotent; current/open statements are provisional and may overlap later closed statements.
- Original statement files are stored in Google Drive after activation, under one flat folder per account. Activate Drive in **Setup → Statements** before uploading or syncing statements.
- Household-aware reads should omit `scope` for personal data and send `scope=household` only for household scope.
- Transaction create/update/delete paths can affect account balances through signals.

## Validation Commands

Backend, from `backend/`:

```bash
ruff check .
ruff format --check .
python manage.py makemigrations --check --dry-run --skip-checks --settings=richtato.settings
python manage.py check --settings=richtato.test_settings
python -m pytest apps/ -v --tb=short
```

Frontend, from `frontend/`:

```bash
yarn lint
yarn format:check
yarn type-check
yarn test:coverage
```

For docs-only changes, review the edited Markdown/rule files for stale paths, routes, ports, and commands. Full app test suites are not required unless code behavior changed.
