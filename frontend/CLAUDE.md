# Frontend Documentation

This file provides guidance when working with the Richtato frontend codebase.

## Project Overview

Richtato is a **Monarch Money competitor** — an AI-native personal finance app with beautiful data visualization, frictionless transaction management, and real-time bank sync. The frontend is a React SPA with responsive design: sidebar navigation on desktop, bottom tab bar on mobile.

## Tech Stack

- **React 19** with TypeScript (strict mode)
- **React Router 7** for client-side routing
- **Vite 6** as build tool with HMR
- **Tailwind CSS 3.4** for styling
- **Shadcn/UI** + **Radix UI** primitives
- **Apache ECharts** (`echarts` + `echarts-for-react`) for all charts
- **TanStack Table** (`@tanstack/react-table`) for data tables
- **Lucide React** for all icons
- **Sonner** for toast notifications
- **date-fns** for date formatting/manipulation
- **Vitest** + **Testing Library** for tests

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

# Formatting
yarn format

# Testing
yarn test
yarn test:run
yarn test:coverage
```

## Directory Structure

```
src/
├── pages/                        # Route-level components
│   ├── ReportPage.tsx            # Net worth & account overview (hero page)
│   ├── BudgetDashboard.tsx       # Budget vs actual, category breakdown
│   ├── Cashflow.tsx              # Income/expense flow visualization
│   ├── DataTable.tsx             # Transaction list with filtering & bulk actions
│   ├── Accounts.tsx              # Account management with history panels
│   ├── Preferences.tsx           # Settings: appearance, categories, budgets
│   ├── Setup.tsx                 # Bank connections & initial account setup
│   ├── More.tsx                  # Mobile-only overflow menu
│   ├── Profile.tsx               # User profile
│   ├── Upload.tsx                # CSV/manual transaction import
│   ├── Welcome.tsx               # Marketing/onboarding landing page
│   ├── Login.tsx                 # Authentication
│   └── Register.tsx              # Registration
│
├── components/
│   ├── Layout.tsx                # Main app layout (header + sidebar + outlet)
│   ├── Sidebar.tsx               # Desktop collapsible navigation
│   ├── BottomTabBar.tsx          # Mobile bottom tab navigation
│   ├── ProtectedRoute.tsx        # Auth-guarded route wrapper
│   ├── ThemeToggle.tsx           # Dark/light mode toggle
│   ├── MobileBottomNav.tsx       # (legacy, prefer BottomTabBar)
│   │
│   ├── asset_dashboard/          # Report page charts & components
│   │   ├── BaseChart.tsx         # Shared ECharts config/wrapper
│   │   ├── NetWorthTrendChart.tsx
│   │   ├── IncomeExpenseChart.tsx
│   │   ├── AssetTrendsChart.tsx
│   │   ├── SavingsChart.tsx
│   │   ├── AccountBreakdownChart.tsx
│   │   ├── AccountsList.tsx
│   │   ├── AccountHistoryPanel.tsx
│   │   ├── GroupHistoryPanel.tsx
│   │   └── MetricCard.tsx        # Key financial metric display card
│   │
│   ├── budget_dashboard/         # Budget page components
│   │   ├── BudgetBreakdown.tsx
│   │   ├── BudgetTrendsChart.tsx
│   │   ├── CategoryBreakdown.tsx
│   │   ├── ExpenseBreakdown.tsx
│   │   ├── PieWithDetailedLegend.tsx
│   │   ├── MonthTimeline.tsx     # Month-by-month navigation
│   │   └── ExpenseDetailModal.tsx
│   │
│   ├── transactions/             # Transaction management
│   │   ├── TransactionTable.tsx  # Main sortable/filterable table
│   │   ├── TransactionForm.tsx   # Create/edit modal
│   │   ├── SearchAndFilter.tsx   # Filter bar
│   │   ├── RecategorizeDialog.tsx       # AI bulk recategorization
│   │   └── RecategorizeProgressModal.tsx
│   │
│   ├── accounts/                 # Account components
│   │   ├── AccountsSidebar.tsx
│   │   ├── AccountDetailPanel.tsx
│   │   ├── AccountFormFields.tsx
│   │   ├── AccountCreateModal.tsx
│   │   └── AccountBalanceForm.tsx
│   │
│   ├── settings/                 # Preferences page sections
│   │   ├── AppearanceSection.tsx
│   │   ├── CategoriesSection.tsx
│   │   ├── BudgetsSection.tsx
│   │   ├── BudgetModal.tsx
│   │   ├── UnifiedAccountsSection.tsx
│   │   ├── AccountDetailModal.tsx
│   │   ├── BulkKeywordsModal.tsx
│   │   ├── NotificationsSection.tsx
│   │   ├── SyncHistorySection.tsx
│   │   └── DisconnectConfirmModal.tsx
│   │
│   └── ui/                       # Shadcn/UI base components
│       ├── button, card, dialog, input, select, switch, tabs
│       ├── badge, avatar, alert, progress, label
│       ├── calendar, date-range-picker, MonthYearPicker, YearPicker
│       ├── DataTable.tsx         # TanStack Table wrapper
│       ├── SortableHeader.tsx    # Table column header with sort
│       ├── ColumnFilterPopover.tsx
│       ├── Pagination.tsx
│       ├── Modal.tsx
│       ├── ContextMenu.tsx
│       ├── LoadingSpinner.tsx
│       ├── dropdown-menu, popover, collapsible, alert-dialog, table
│
├── lib/
│   ├── api/                      # API service singletons
│   │   ├── auth.ts               # Login, logout, demo, register
│   │   ├── transactions.ts       # Transactions & categories
│   │   ├── asset-dashboard.ts    # Net worth metrics & trends
│   │   ├── budget-dashboard.ts   # Budget analytics
│   │   ├── bankConnections.ts    # Bank sync management (Plaid/Teller)
│   │   ├── user.ts               # User profile & settings
│   │   └── csrf.ts               # CSRF token handling
│   └── utils.ts                  # cn(), currency formatting, date utils
│
├── contexts/
│   ├── AuthContext.tsx            # Auth state + login/logout/checkAuth
│   ├── PreferencesContext.tsx     # Currency, date format, display prefs
│   └── ThemeContext.tsx           # Dark/light mode
│
├── hooks/
│   ├── useAuth.ts                 # Auth context consumer
│   ├── useSyncStatus.ts           # Bank sync polling + callbacks
│   ├── usePlaidLink.ts            # Plaid Link integration
│   └── usePolling.ts              # Generic polling hook
│
└── types/                         # Shared TypeScript type definitions
```

## API Service Pattern

All API calls use class-based service singletons in `lib/api/`:

```typescript
class TransactionService {
  private baseUrl = '/api/v1';

  async getTransactions(
    filters: TransactionFilters
  ): Promise<TransactionResponse> {
    const response = await fetch(`${this.baseUrl}/transactions/?${params}`, {
      credentials: 'include',
      headers: this.getHeaders(),
    });
    return this.handleResponse(response);
  }

  async updateTransaction(id: number, data: UpdateData): Promise<Transaction> {
    const csrf = await getCSRFToken();
    const response = await fetch(`${this.baseUrl}/transactions/${id}/`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrf, ...this.getHeaders() },
      body: JSON.stringify(data),
    });
    return this.handleResponse(response);
  }
}

export const transactionService = new TransactionService();
```

**Rules:**

- Services are singleton instances — import the instance, not the class
- `credentials: 'include'` on every request (cookie-based auth)
- CSRF token via `getCSRFToken()` on all mutations (POST/PUT/PATCH/DELETE)
- `handleResponse()` for consistent error handling

## State Management

| Layer              | Tool                 | Use Case                      |
| ------------------ | -------------------- | ----------------------------- |
| Global auth        | `AuthContext`        | login state, user object      |
| Global preferences | `PreferencesContext` | currency, date format         |
| Theme              | `ThemeContext`       | dark/light                    |
| Filter state       | URL search params    | date ranges, category filters |
| Local UI           | `useState`           | modals, loading, form state   |

## Data Fetching Pattern

```typescript
useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await someService.getData(filters);
      setData(data);
    } catch (error) {
      setError('Failed to load');
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, [filters]);
```

## Charts (ECharts)

All charts use `echarts-for-react`. Reference `BaseChart.tsx` for shared setup.

```typescript
import ReactECharts from 'echarts-for-react';

const option = {
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: labels },
  yAxis: { type: 'value' },
  series: [{ type: 'line', data: values, smooth: true }],
};

<ReactECharts option={option} style={{ height: '300px' }} />
```

**Chart guidelines:**

- Use `smooth: true` for line charts (Monarch aesthetic)
- Pass theme-aware colors — read from CSS variables or accept as props
- Always set explicit `height` on the wrapper style
- Use `tooltip.formatter` to show currency values with the user's preferred format

## Tables (TanStack Table)

The `ui/DataTable.tsx` component wraps TanStack Table. Use `SortableHeader` for sortable columns and `ColumnFilterPopover` for column-level filtering.

```typescript
import { DataTable } from '@/components/ui/DataTable';

const columns: ColumnDef<Transaction>[] = [
  {
    accessorKey: 'date',
    header: ({ column }) => <SortableHeader column={column} title="Date" />,
  },
  // ...
];

<DataTable columns={columns} data={transactions} />
```

## Component Conventions

### Imports

```typescript
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { TrendingUp, DollarSign } from 'lucide-react';
```

### Conditional Classes

```typescript
<div className={cn(
  'base-classes',
  isActive && 'active-classes',
  variant === 'secondary' && 'secondary-classes'
)}>
```

### Toasts (Sonner)

```typescript
import { toast } from 'sonner';

toast.success('Sync complete', { description: '12 new transactions' });
toast.error('Failed to sync', { description: error.message });
```

### Loading States

Use `animate-shimmer` skeleton divs for loading states, matching the shape of the loaded content. Avoid full-page spinners for data fetches.

## Responsive Design

The app uses a **sidebar + bottom tab bar** pattern:

```
Desktop (md+):         Mobile (<md):
┌────────┬──────────┐  ┌──────────────┐
│Sidebar │  Content │  │   Header     │
│        │          │  │   Content    │
│        │          │  │              │
└────────┴──────────┘  │──────────────│
                       │  Bottom Tabs │
                       └──────────────┘
```

- `Sidebar`: `hidden md:flex` — only visible on desktop
- `BottomTabBar`: `md:hidden fixed bottom-0` — only visible on mobile
- Main content: `pb-20 md:pb-6` — extra bottom padding on mobile for tab bar clearance
- Header: sticky, `bg-background/95 backdrop-blur` for scroll effect

## UX Patterns (Monarch-inspired)

- **Metric cards**: Large number + label + trend indicator. Use `MetricCard` component.
- **Month navigation**: `MonthTimeline` for budget and cashflow time navigation
- **Inline editing**: Click-to-edit on transaction rows rather than navigating away
- **Bulk actions**: Select multiple transactions → bulk categorize, delete
- **AI recategorization**: `RecategorizeDialog` triggers backend AI to re-classify transactions
- **Sync status badge**: Emerald badge on Data tab shows new transaction count after sync
- **Positive = emerald, negative = destructive**: Consistent across all money displays

## Configuration

| File                 | Purpose                                                          |
| -------------------- | ---------------------------------------------------------------- |
| `vite.config.ts`     | Build config, path aliases (`@/` → `src/`), dev proxy to backend |
| `tailwind.config.js` | Theme, custom animations, typography plugin                      |
| `tsconfig.json`      | TypeScript strict mode                                           |
| `eslint.config.js`   | ESLint flat config                                               |

## Development Notes

- **Port**: Dev server runs on port 5927
- **Auth**: Cookie-based session with CSRF protection
- **API Proxy**: Vite proxies `/api/` to backend in development
- **Path Alias**: Always use `@/` for imports from `src/`
- **No console.log**: Use proper error boundaries or silent failure with toast
