# Richtato - Refactored Architecture

This repository has been refactored to separate the frontend (React) and backend (Django) components for better maintainability and scalability.

## Architecture Overview

### Frontend (React + TypeScript + Vite)

- **Location**: `/frontend/`
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + Custom components
- **Charts**: Chart.js
- **State Management**: React Context + Hooks

### Backend (Django + DRF)

- **Location**: `/richtato/`
- **Framework**: Django 5.1
- **API**: Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **CORS**: django-cors-headers

## Project Structure

```
richtato/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities and API clients
│   │   └── types/           # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── richtato/                 # Django backend
│   ├── apps/                # Django apps
│   ├── richtato/            # Django project settings
│   └── manage.py
├── build-frontend.sh        # Build script
└── dev-start.sh            # Development script
```

## Development Setup

### Prerequisites

- Node.js 18+ and Yarn
- Python 3.8+ and pip
- Git

### Installation

1. **Backend Setup**:

   ```bash
   cd richtato
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   yarn install
   ```

### Development

**Option 1: Run both servers together**

```bash
./dev-start.sh
```

**Option 2: Run separately**

```bash
# Terminal 1 - Django backend
cd richtato
python manage.py runserver 8000

# Terminal 2 - React frontend
cd frontend
yarn dev
```

### Production Build

```bash
./build-frontend.sh
cd richtato
python manage.py runserver 8000
```

## API Endpoints

All API endpoints are prefixed with `/api/`:

- **Authentication**: `/api/auth/`
- **Dashboard**: `/api/dashboard/`
- **Accounts**: `/api/accounts/`
- **Transactions**: `/api/transactions/`
- **Budget**: `/api/budget/`

## Key Features Migrated

### Dashboard

- ✅ KPI metrics (Net Worth, Savings Rate, Budget Utilization)
- ✅ Budget progress visualization
- ✅ Income vs Expenses charts
- ✅ Savings accumulation tracking
- ✅ Top spending categories
- ✅ Expense breakdown pie chart
- ✅ Accounts overview
- ✅ Cash flow visualization

### Pages

- ✅ Login/Register with form validation
- ✅ Dashboard with interactive charts
- ✅ Data table with filtering and search
- ✅ File upload with progress tracking
- ✅ User profile management
- ✅ Settings with preferences

### Components

- ✅ Responsive sidebar navigation
- ✅ Theme toggle (light/dark mode)
- ✅ Reusable chart components
- ✅ Form components with validation
- ✅ Modal dialogs and notifications

## Migration Notes

### From Django Templates to React Components

- HTML templates → React JSX components
- Django template tags → React props and state
- Server-side rendering → Client-side rendering
- Django forms → React form components with validation

### From Django Views to API Endpoints

- Template views → API views returning JSON
- Form handling → REST API endpoints
- Session-based auth → Token-based auth (future enhancement)

### From jQuery to React

- DOM manipulation → React state management
- Event handling → React event handlers
- AJAX calls → React hooks and API clients

## Next Steps

1. **API Integration**: Connect React components to Django API endpoints
2. **Authentication**: Implement proper JWT or session-based auth
3. **Real-time Updates**: Add WebSocket support for live data
4. **Testing**: Add unit and integration tests
5. **Deployment**: Set up CI/CD pipeline
6. **Performance**: Optimize bundle size and loading times

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure the frontend URL is added to `CORS_ALLOWED_ORIGINS` in Django settings.

### Build Issues

Make sure all dependencies are installed:

```bash
cd frontend && yarn install
cd ../richtato && pip install -r requirements.txt
```

### Database Issues

Run migrations if you encounter database errors:

```bash
cd richtato
python manage.py migrate
```
