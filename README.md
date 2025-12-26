# Richtato - Personal Finance Management Platform

A comprehensive personal finance management application for tracking expenses, income, budgets, and net worth. Features bank account syncing, AI-powered categorization, and interactive dashboards.

## Features

- **Transaction Tracking**: Track all financial transactions with automatic categorization
- **Bank Sync**: Connect bank accounts via Plaid for automatic transaction import
- **Budget Management**: Set and monitor budgets by category with visual progress
- **Net Worth Dashboard**: Track assets, liabilities, and net worth over time
- **AI Categorization**: Intelligent transaction categorization using OpenAI
- **Interactive Charts**: Visualize spending patterns, trends, and cash flow
- **Multi-Account Support**: Checking, savings, credit cards, investments
- **Demo Mode**: Try the application with sample data

## Tech Stack

### Backend
- **Django 5.x** with Django REST Framework
- **PostgreSQL** database
- **Gunicorn** WSGI server
- **OpenAI** for AI categorization
- **Plaid** for bank sync

### Frontend
- **React 19** with TypeScript
- **Vite 7** build tool
- **Tailwind CSS** for styling
- **Shadcn/UI** component library
- **Lucide React** icons

### Infrastructure
- **Docker** containerization
- **Nginx** reverse proxy (production)

## Project Structure

```
richtato/
├── backend/
│   ├── apps/                    # Django applications
│   │   ├── transaction/         # Transactions and categories
│   │   ├── financial_account/   # Bank accounts and balances
│   │   ├── budget/              # Budget management
│   │   ├── budget_dashboard/    # Budget analytics
│   │   ├── asset_dashboard/     # Net worth and metrics
│   │   ├── sync/                # Bank sync (Plaid)
│   │   ├── categorization/      # AI categorization
│   │   ├── richtato_user/       # User management
│   │   └── core/                # Shared utilities
│   ├── integrations/            # External API clients
│   │   └── plaid/               # Plaid API
│   ├── artificial_intelligence/ # OpenAI integration
│   ├── statement_imports/       # Bank statement parsers
│   ├── richtato/                # Django settings
│   └── config/                  # Configuration files
├── frontend/
│   ├── src/
│   │   ├── pages/               # Route components
│   │   ├── components/          # UI components
│   │   ├── lib/api/             # API services
│   │   ├── contexts/            # React contexts
│   │   └── hooks/               # Custom hooks
│   └── public/                  # Static assets
├── .cursorrules                 # AI assistant context
├── API_REFERENCE.md             # API documentation
└── docker-compose.yml           # Docker configuration
```

## Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd richtato

# Copy environment template
cp env.template .env
# Edit .env with your configuration

# Start all services
docker compose up -d

# Access the application
open http://localhost:5927
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Set up database
createdb richtato_db
python manage.py migrate

# Run server
python manage.py runserver
```

#### Frontend

```bash
cd frontend

# Install dependencies
yarn install

# Run development server
yarn dev
```

## Environment Variables

```bash
# Backend
SECRET_KEY=your_django_secret_key
DATABASE_URL=postgresql://user:password@localhost/richtato_db
OPENAI_API_KEY=your_openai_api_key

# Bank Sync (optional)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret

# Deployment
DEPLOY_STAGE=DEV  # or PROD
```

## Development

### Commands

```bash
# Backend
docker compose logs -f backend
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py migrate

# Frontend
yarn dev          # Development server
yarn build        # Production build
yarn lint         # Run linter
yarn type-check   # TypeScript check
```

### Architecture

The backend follows a **Repository → Service → View** pattern:
- **Views**: Thin HTTP handlers
- **Services**: Business logic
- **Repositories**: Database access

See `backend/CLAUDE.md` for detailed backend documentation.

The frontend uses a **Page → Component → API Service** pattern:
- **Pages**: Route-level components
- **Components**: Reusable UI elements
- **API Services**: Backend communication

See `frontend/CLAUDE.md` for detailed frontend documentation.

## API Documentation

See [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation.

Key endpoints:
- `/api/v1/auth/` - Authentication
- `/api/v1/transactions/` - Transaction management
- `/api/v1/accounts/` - Account management
- `/api/v1/budgets/` - Budget management
- `/api/v1/asset-dashboard/` - Net worth metrics
- `/api/v1/budget-dashboard/` - Budget analytics
- `/api/v1/sync/` - Bank sync

## Deployment

### Docker (Single Container)

```bash
# Build production image
./scripts/build.sh richtato:latest

# Run with environment variables
docker run -p 10000:10000 \
  -e SECRET_KEY=... \
  -e DATABASE_URL=... \
  richtato:latest
```

### Render

1. Create a Render Web Service (Docker)
2. Set build arg: `VITE_API_BASE_URL=/api`
3. Configure environment variables
4. Deploy

## Testing

```bash
# Backend tests
docker compose exec backend python manage.py test

# Frontend tests
cd frontend && yarn test
```

## License

MIT License - see LICENSE file for details.
