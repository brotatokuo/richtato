# Frontend Documentation

This file provides guidance when working with the Richtato frontend codebase.

## Project Overview

Richtato Frontend is a **React-based personal finance management interface** providing dashboards for tracking expenses, income, budgets, and net worth. It connects to a Django backend API for data and supports bank account syncing.

## Tech Stack

- **React 19** with TypeScript
- **React Router 7** for client-side routing
- **Vite 7** as build tool with HMR
- **Tailwind CSS 3.4** for styling
- **Shadcn/UI** component library
- **Lucide React** for icons
- **Vitest** for testing

## Development Commands

```bash
# Install dependencies
yarn install

# Start development server (port 5927)
yarn dev

# Build for production
yarn build

# Type checking
yarn type-check

# Linting
yarn lint
yarn lint:fix

# Testing
yarn test
yarn test:run
yarn test:coverage
```

## Directory Structure

```
src/
├── pages/              # Route-level components
│   ├── AssetDashboard.tsx     # Net worth & account overview
│   ├── BudgetDashboard.tsx    # Budget tracking & trends
│   ├── Cashflow.tsx           # Income/expense flow
│   ├── Transactions.tsx       # Transaction list & management
│   ├── Settings.tsx           # App settings & preferences
│   ├── Login.tsx              # Authentication
│   └── Profile.tsx            # User profile
│
├── components/         # Reusable UI components
│   ├── Layout.tsx             # Main app layout with sidebar
│   ├── Sidebar.tsx            # Navigation sidebar
│   ├── ProtectedRoute.tsx     # Auth-guarded route wrapper
│   ├── ThemeToggle.tsx        # Dark/light mode toggle
│   ├── ui/                    # Shadcn/UI base components
│   ├── asset_dashboard/       # Asset/net worth charts
│   ├── budget_dashboard/      # Budget visualization
│   ├── transactions/          # Transaction table & forms
│   ├── accounts/              # Account cards & modals
│   └── settings/              # Settings panels & modals
│
├── lib/
│   ├── api/            # API service classes
│   │   ├── auth.ts            # Login, logout, demo
│   │   ├── transactions.ts    # Transactions & categories
│   │   ├── asset-dashboard.ts # Net worth metrics
│   │   ├── budget-dashboard.ts# Budget analytics
│   │   ├── bankConnections.ts # Bank sync management (Plaid)
│   │   ├── user.ts            # User profile & settings
│   │   └── csrf.ts            # CSRF token handling
│   └── utils.ts        # Utility functions (cn, formatting)
│
├── contexts/           # React Context providers
│   ├── AuthContext.tsx        # Authentication state
│   ├── PreferencesContext.tsx # User preferences
│   └── ThemeContext.tsx       # Theme management
│
├── hooks/              # Custom React hooks
│   └── usePlaidLink.ts        # Plaid bank connection
│
└── types/              # TypeScript type definitions
```

## API Service Pattern

All API calls use class-based services in `lib/api/`:

```typescript
// Example: transactions.ts
class TransactionService {
  private baseUrl = '/api/v1';

  async getTransactions(filters: TransactionFilters): Promise<TransactionResponse> {
    const response = await fetch(`${this.baseUrl}/transactions/`, {...});
    return this.handleResponse(response);
  }

  async updateTransaction(id: number, data: UpdateData): Promise<Transaction> {
    const csrf = await getCSRFToken();
    const response = await fetch(`${this.baseUrl}/transactions/${id}/`, {
      method: 'PUT',
      headers: { 'X-CSRFToken': csrf, ...this.getHeaders() },
      body: JSON.stringify(data),
    });
    return this.handleResponse(response);
  }
}

export const transactionService = new TransactionService();
```

**Key patterns:**

- Services are singleton instances exported from each file
- CSRF tokens fetched via `getCSRFToken()` for mutations
- `handleResponse()` method for consistent error handling
- Credentials: 'include' for cookie-based auth

## State Management

### Authentication (`AuthContext`)

- Manages user login state
- Provides `login()`, `logout()`, `checkAuth()` methods
- Handles demo user creation

### Preferences (`PreferencesContext`)

- User display preferences (date format, currency)
- Persisted via backend API

### Local State

- Component-level `useState` for UI state
- URL search params for filters (date ranges, categories)

## Component Conventions

### Imports

```typescript
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { ChevronRight, DollarSign } from 'lucide-react';
```

### Conditional Classes

```typescript
<div className={cn(
  "base-classes",
  isActive && "active-classes",
  variant === "secondary" && "secondary-classes"
)}>
```

### Data Fetching

```typescript
useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await someService.getData();
      setData(data);
    } catch (error) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, [dependency]);
```

## Key Pages

| Page              | Purpose                                              |
| ----------------- | ---------------------------------------------------- |
| `AssetDashboard`  | Net worth overview, account breakdown, trends        |
| `BudgetDashboard` | Budget progress, spending by category                |
| `Transactions`    | Transaction list with filtering, bulk categorization |
| `Cashflow`        | Income vs expense visualization                      |
| `Settings`        | Accounts, categories, budgets, bank connections      |

## Component Features

### Asset Dashboard (`components/asset_dashboard/`)

- `MetricCard` - Key financial metrics display
- `NetWorthTrendChart` - Line chart of net worth over time
- `AccountsList` - Grouped accounts with balances
- `IncomeExpenseChart` - Income vs expense comparison

### Budget Dashboard (`components/budget_dashboard/`)

- `BudgetBreakdown` - Budget allocation by category
- `ExpenseBreakdown` - Spending breakdown pie chart
- `MonthTimeline` - Month-by-month navigation

### Transactions (`components/transactions/`)

- `TransactionTable` - Sortable, filterable transaction list
- `TransactionForm` - Create/edit transaction modal
- `RecategorizeDialog` - Bulk AI re-categorization

### Settings (`components/settings/`)

- `CategoriesSection` - Manage transaction categories
- `BudgetsSection` - Budget allocation management
- `BankConnectionsSection` - Bank connection management
- `UnifiedAccountsSection` - Account overview

## UI Components (`components/ui/`)

Based on Shadcn/UI, includes:

- `Button`, `Card`, `Dialog`, `Modal`
- `Input`, `Select`, `Switch`, `Calendar`
- `Table`, `DataTable` (with sorting/filtering)
- `DropdownMenu`, `Popover`, `ContextMenu`

## Configuration

| File                 | Purpose                                    |
| -------------------- | ------------------------------------------ |
| `vite.config.ts`     | Build config, path aliases (`@/` → `src/`) |
| `tailwind.config.js` | Theme customization                        |
| `tsconfig.json`      | TypeScript with strict mode                |
| `eslint.config.js`   | ESLint flat config                         |

## Development Notes

- **Port**: Development server runs on port 5927
- **Auth**: Cookie-based with CSRF protection
- **API Proxy**: Vite proxies `/api/` to backend in dev
- **Path Alias**: Use `@/` for imports from `src/`
