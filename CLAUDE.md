# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Richtato is a Django-based personal finance management application with features for tracking expenses, income, budgets, and financial accounts. It includes AI-powered categorization using Google Gemini and supports multiple bank statement imports.

## Development Commands

### Setup and Dependencies
```bash
# Initial setup (run from project root)
./run.sh

# Manual setup (from richtato/ directory)
cd richtato
npm install
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:$PORT
```

### Django Management Commands
```bash
# Navigate to Django project directory first
cd richtato

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Development server
python manage.py runserver
python manage.py runserver 0.0.0.0:8000

# Shell access
python manage.py shell

# Collect static files (if needed)
python manage.py collectstatic
```

### Frontend Dependencies
```bash
# Install JavaScript dependencies (from richtato/ directory)
npm install
```

## Architecture

### Django Apps Structure
- **richtato_user**: Core user management, authentication, categories, and card accounts
- **account**: Financial account management and transactions
- **budget**: Budget planning and tracking
- **income**: Income recording and management
- **expense**: Expense tracking with AI categorization
- **settings**: Application settings and self-ping middleware

### Key Components
- **AI Integration**: `artificial_intelligence/ai.py` - Google Gemini for expense categorization
- **Statement Imports**: `statement_imports/` - Bank-specific CSV parsers (Chase, Citi, AmEx, BoA)
- **Categories**: `categories/` - Category management and AI-powered categorization
- **Database**: Multi-environment support (SQLite for LOCAL, PostgreSQL for DEV/PROD)

### Environment Configuration
The app uses `DEPLOY_STAGE` environment variable:
- `LOCAL`: SQLite database, development settings
- `DEV`: PostgreSQL database, development deployment
- `PROD`: PostgreSQL database, production deployment

### Frontend
- Static files in `static/` directory
- Templates in `pages/` directory
- JavaScript modules for different features (dashboard, budget, graphs, etc.)
- Uses DataTables for table management

### Database Models
- Custom User model in `richtato_user` app
- Financial entities: Account, Income, Expense, Budget
- Category system with AI-powered classification
- Transaction tracking across different account types

## File Structure Notes
- Main Django project: `richtato/richtato/`
- Apps: `richtato/apps/` (note: some apps use `richtato.apps.` prefix in URLs)
- Static assets: `richtato/static/`
- Templates: `richtato/pages/`
- Database utilities: `utilities/postgres/`

## Testing
No specific test commands found in configuration files. Use standard Django testing:
```bash
cd richtato
python manage.py test
```
