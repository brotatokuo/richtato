# Richtato

Richtato is an AI-native personal finance app for tracking transactions, budgets, account balances, net worth, household finances, bank sync, and AI-powered categorization.

The product goal is Monarch Money quality: clean financial dashboards, fast transaction workflows, helpful automation, responsive desktop/mobile navigation, and strong dark/light mode parity.

## Features

- Transaction tracking with categories, filters, bulk actions, and AI recategorization.
- Google Drive statement storage and a Chrome-extension-driven bank automation flow for hands-off downloads.
- Net worth and cash flow dashboard with ECharts visualizations.
- Budget tracking by month, category, and household scope.
- Household sharing for shared accounts and household budgets.
- User preferences for display, currency, appearance, categories, and account settings.
- Demo mode for quickly exploring populated data.
- Statement import with row-level deduplication and Drive-backed original file retention, organized as one flat folder per account.

## Tech Stack

| Area | Stack |
| --- | --- |
| Backend | Django 5.x, Django REST Framework, PostgreSQL, Gunicorn, Loguru |
| Frontend | React 19, TypeScript, Vite 6, React Router 7, Tailwind CSS 3.4 |
| UI | Shadcn/Radix primitives, Lucide icons, Sonner toasts |
| Data viz | Apache ECharts, TanStack Table |
| Integrations | Chrome-extension bank automation for sync, OpenAI for categorization |
| Infrastructure | Docker Compose locally, single-container production build |

## Project Structure

```text
richtato/
├── AGENTS.md                 # AI-agent orientation
├── API_REFERENCE.md          # HTTP API reference
├── backend/
│   ├── apps/                 # Django apps
│   ├── integrations/         # External integrations and helpers
│   ├── artificial_intelligence/
│   ├── config/
│   └── richtato/             # Django settings and root URLs
├── frontend/
│   ├── src/pages/            # Route-level React pages
│   ├── src/components/       # Feature and UI components
│   ├── src/contexts/         # Global React contexts
│   ├── src/hooks/
│   └── src/lib/api/          # API service singletons
├── scripts/
├── cli/
└── docker-compose.yml
```

## Quick Start

```bash
cp env.template .env
docker compose up -d
open http://localhost:3000
```

The frontend dev server runs on port `3000` and proxies `/api/` plus `/demo-login` to the backend.

Useful Docker commands:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell
docker compose restart backend frontend
```

## Manual Development

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
yarn install
yarn dev
```

## Current App Routes

- Public: `/welcome`, `/login`, `/register`.
- Protected: `/dashboard`, `/accounts`, `/budget`, `/transactions`, `/setup`, `/preferences`, `/profile`, `/household`, `/formulas`, `/more`.
- Redirects: `/` to `/dashboard`, `/cashflow` to `/dashboard`, `/settings` to `/preferences`.

## API Documentation

Primary API endpoints are under `/api/v1/`; many also exist under `/api/` for compatibility. See `API_REFERENCE.md` for the maintained reference and `/api/docs/` for Swagger when the backend is running.

Key roots:

- `/api/v1/auth/`
- `/api/v1/accounts/` — includes Drive statement storage, agent uploads, and statement record APIs
- `/api/v1/transactions/`
- `/api/v1/budgets/`
- `/api/v1/asset-dashboard/`
- `/api/v1/budget-dashboard/`
- `/api/v1/sync/`
- `/api/v1/household/`

## Validation

Backend checks from `backend/`:

```bash
ruff check .
ruff format --check .
python manage.py makemigrations --check --dry-run --skip-checks --settings=richtato.settings
python manage.py check --settings=richtato.test_settings
python -m pytest apps/ -v --tb=short
```

Frontend checks from `frontend/`:

```bash
yarn lint
yarn format:check
yarn type-check
yarn test:coverage
```

## Agent And Developer Docs

- `AGENTS.md` explains where AI agents should look first.
- `.cursor/rules/` contains focused Cursor rules.
- `frontend/CLAUDE.md` documents frontend architecture and patterns.
- `backend/CLAUDE.md` documents backend architecture and patterns.
- `API_REFERENCE.md` documents the HTTP API.

## Deployment

Build and run the production container with environment variables:

```bash
./scripts/build.sh richtato:latest
docker run -p 10000:10000 --env-file .env richtato:latest
```

Render deployments should set `VITE_API_BASE_URL=/api` at build time and provide the backend environment variables from `env.template`.
