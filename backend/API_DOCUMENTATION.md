# Richtato Backend API Documentation

## Overview

The Richtato backend has been cleaned up to focus exclusively on API functionality, removing all frontend-related files and template-based views. The API is now fully documented with Swagger/OpenAPI specifications.

## API Documentation

- **Swagger UI**: `/swagger/` - Interactive API documentation
- **ReDoc**: `/redoc/` - Alternative API documentation format
- **OpenAPI JSON**: `/swagger.json` - Raw OpenAPI specification

## API Endpoints

### Authentication (`/api/auth/`)

- `POST /login/` - User login
- `POST /register/` - User registration
- `POST /logout/` - User logout
- `GET /profile/` - Get user profile
- `POST /check-username/` - Check username availability
- `POST /update-username/` - Update username
- `POST /change-password/` - Change password
- `POST /update-preferences/` - Update user preferences
- `POST /delete-account/` - Delete user account

### User Data (`/api/auth/`)

- `GET /timeseries-data/` - Get income/expense time series data
- `GET /categories/` - Get user categories
- `POST /categories/` - Create new category
- `PUT /categories/<id>/` - Update category
- `DELETE /categories/<id>/` - Delete category
- `GET /categories/field-choices/` - Get category field choices
- `GET /card-accounts/` - Get user card accounts

### Budget Management (`/api/budget/`)

- `GET /` - Get budget entries
- `POST /` - Create budget entry
- `GET /<id>/` - Get specific budget entry
- `PATCH /<id>/` - Update budget entry
- `DELETE /<id>/` - Delete budget entry
- `GET /field-choices/` - Get budget field choices
- `GET /rankings/` - Get budget rankings

### Expense Management (`/api/expense/`)

- `GET /` - Get expense entries
- `POST /` - Create expense entry
- `GET /<id>/` - Get specific expense entry
- `PATCH /<id>/` - Update expense entry
- `DELETE /<id>/` - Delete expense entry
- `GET /field-choices/` - Get expense field choices
- `GET /graph/` - Get expense graph data
- `POST /categorize-transaction/` - AI-powered transaction categorization
- `POST /import-statements/` - Import bank statements

### Account Management (`/api/accounts/`)

- `GET /` - Get accounts
- `POST /` - Create account
- `GET /<id>/` - Get specific account
- `PATCH /<id>/` - Update account
- `DELETE /<id>/` - Delete account
- `GET /field-choices/` - Get account field choices
- `GET /details/` - Get account details
- `GET /details/field-choices/` - Get detail field choices
- `GET /details/<id>/` - Get specific account detail
- `GET /<id>/transactions/` - Get account transactions

### Income Management (`/api/income/`)

- `GET /` - Get income entries
- `POST /` - Create income entry
- `GET /<id>/` - Get specific income entry
- `PATCH /<id>/` - Update income entry
- `DELETE /<id>/` - Delete income entry
- `GET /field-choices/` - Get income field choices

### Dashboard Data (`/api/dashboard/`)

- `GET /cash-flow/` - Get cash flow data
- `GET /expense-categories/` - Get expense categories data
- `GET /income-expenses/` - Get income vs expenses data
- `GET /savings/` - Get savings data
- `GET /budget-progress/` - Get budget progress data
- `GET /top-categories/` - Get top spending categories
- `GET /expense-years/` - Get available expense years
- `GET /sankey-data/` - Get Sankey diagram data

### Settings (`/api/settings/`)

- Settings management endpoints

## Removed Components

- All HTML templates and template-based views
- Static frontend files (CSS, JS, images)
- Frontend-specific context processors
- Template rendering configurations
- Node.js dependencies

## Key Features

- **RESTful API Design**: All endpoints follow REST conventions
- **Swagger Documentation**: Comprehensive API documentation
- **Authentication**: Session-based authentication
- **CORS Support**: Configured for React frontend
- **Pagination**: Built-in pagination for list endpoints
- **Filtering & Search**: Search and ordering capabilities
- **AI Integration**: Transaction categorization using AI
- **File Upload**: Statement import functionality

## Development

- **Admin Panel**: Available at `/admin/`
- **Demo Login**: Available at `/demo-login/` for development
- **API Testing**: Use Swagger UI for interactive testing

## Dependencies

All dependencies are managed through `pyproject.toml` in the backend directory (modern Python packaging standard):

**Core Framework:**

- Django 5.1
- Django REST Framework 3.14.0
- drf-yasg 1.21.7 (Swagger documentation)
- django-cors-headers 4.3.1

**Database:**

- psycopg2-binary 2.9.7 (PostgreSQL adapter)
- SQLite (development default)

**Additional Libraries:**

- pandas 2.1.4 (data processing)
- numpy 1.24.3 (numerical computing)
- plotly 5.17.0 (data visualization)
- openai 1.3.0 (AI integration)
- gunicorn 21.2.0 (production server)

**Installation:**

```bash
cd backend
pip install -e .
```
