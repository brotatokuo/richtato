# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Essential Commands
- **Start development server**: `./run.sh` (runs migrations and starts server on 0.0.0.0:$PORT)
- **Manual development server**: `cd richtato && python manage.py runserver`
- **Database migrations**: `cd richtato && python manage.py makemigrations && python manage.py migrate`
- **Create demo data**: `./create_or_reset_demo.sh`
- **Run tests**: `cd richtato && python manage.py test`
- **Install dependencies**: `pip install -e .` (from project root)
- **Frontend dependencies**: `cd richtato && npm install`

### Environment Setup
- Uses environment-based configuration (`DEPLOY_STAGE=DEV/PROD/LOCAL`)
- SQLite for local development, PostgreSQL for production
- Requires `.env` file for production settings (DATABASE_URL, OPENAI_API_KEY, SECRET_KEY)

## Project Architecture

### High-Level Structure
This is a Django-based personal finance management web application with a modular app-based architecture. Each financial feature is implemented as a separate Django app under `richtato/apps/`.

### Core Django Apps
- **`richtato_user/`**: Custom user model with financial preferences and demo user factory
- **`account/`**: Bank account, credit card, and investment account management
- **`expense/`**: Transaction tracking with AI-powered categorization
- **`income/`**: Income source management and tracking
- **`budget/`**: Category-based budget planning and progress monitoring
- **`dashboard/`**: Analytics views and data visualization endpoints
- **`settings/`**: Application middleware and configuration

### Key Supporting Systems
- **`categories/`**: Centralized category system with icons, colors, and smart matching rules
- **`statement_imports/`**: Pluggable bank statement import system with card-specific parsers
- **`artificial_intelligence/`**: AI integration layer for transaction categorization using OpenAI
- **`utilities/`**: Shared utility functions and database helpers

### Frontend Architecture
- **Server-rendered templates** in `pages/` with progressive JavaScript enhancement
- **Component-based JavaScript** in `static/js/` (RichTable, BudgetRenderer, etc.)
- **API-driven updates** using Django REST Framework endpoints
- **Chart.js and Plotly.js** for interactive visualizations and Sankey diagrams

### Database Design Patterns
- **Multi-account support**: Users can have multiple bank accounts, credit cards, investments
- **Transaction categorization**: AI-powered and rule-based expense categorization
- **Extensible category system**: Categories defined with icons, colors, and keyword matching
- **Budget tracking**: Real-time budget progress calculation across categories

## Key Development Patterns

### Adding New Bank/Card Support
1. Create new importer in `statement_imports/cards/[bank_name].py`
2. Follow the factory pattern used in existing importers
3. Register the importer in the card canonicalizer system
4. Add specific CSV/Excel parsing logic for the bank's format

### Extending Categories
1. Modify `categories/categories.py` to add new category definitions
2. Include icon (Font Awesome), color (hex), and keyword matching rules
3. Categories are automatically available across all apps

### Creating New Financial Features
1. Create new Django app under `richtato/apps/[feature_name]/`
2. Define models with proper foreign key relationships to User and Account
3. Create API endpoints using Django REST Framework
4. Add frontend components in `static/js/components/`
5. Register app in `settings.py` INSTALLED_APPS

### AI Integration
- OpenAI integration is centralized in `artificial_intelligence/ai.py`
- Transaction categorization uses GPT models with expense context
- AI features are optional and degrade gracefully without API keys

## Important File Locations

### Configuration
- **Django settings**: `richtato/richtato/settings.py`
- **URL routing**: `richtato/richtato/urls.py`
- **Dependencies**: `pyproject.toml` (Python), `richtato/package.json` (Node.js)

### Core Data Models
- **User model**: `richtato/apps/richtato_user/models.py`
- **Account models**: `richtato/apps/account/models.py`
- **Transaction models**: `richtato/apps/expense/models.py`
- **Category definitions**: `richtato/categories/categories.py`

### Frontend Assets
- **JavaScript components**: `richtato/static/js/components/`
- **API utilities**: `richtato/static/js/utils/api.js`
- **Chart configurations**: `richtato/static/js/charts/`
- **CSS styles**: `richtato/static/css/`

### Templates
- **HTML templates**: `richtato/pages/`
- **Base template**: `richtato/pages/base.html`

## Development Guidelines

### Code Organization
- Follow Django's MVT (Model-View-Template) pattern
- Each feature should be self-contained within its app
- Shared utilities go in `utilities/`
- Frontend components are modular and reusable

### Database Interactions
- Use Django ORM for all database operations
- Models include comprehensive docstrings and field documentation
- Foreign key relationships maintain data integrity
- JSON fields are used for flexible metadata storage

### Frontend Development
- Progressive enhancement: server-rendered pages work without JavaScript
- API calls use consistent error handling patterns
- Charts and visualizations are responsive and interactive
- DataTables integration provides sortable, editable data grids

### Testing Strategy
- Django's built-in test framework
- Tests are organized by app in `tests.py` files
- Run tests with `python manage.py test` from `richtato/` directory
- Test coverage tracking available with `coverage` package

### Security Considerations
- CSRF protection enabled for all forms
- User authentication required for all financial data
- Input validation and sanitization implemented
- Demo mode isolates test data from production
