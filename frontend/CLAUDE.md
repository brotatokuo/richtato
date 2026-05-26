# Frontend Guide

This file documents the current Richtato frontend patterns for agents and developers.

## Overview

The frontend is a React SPA for an AI-native personal finance app. It prioritizes polished dashboards, fast transaction workflows, household-aware data, and responsive navigation: desktop sidebar plus mobile bottom tabs.

## Stack

- React 19 with TypeScript strict mode.
- React Router 7.
- Vite 6 on port `3000`.
- Tailwind CSS 3.4 with Shadcn/Radix primitives.
- ECharts through `echarts-for-react`.
- TanStack Table for data grids.
- Lucide icons, Sonner toasts, date-fns.
- Vitest and Testing Library.

## Commands

```bash
yarn install
yarn dev
yarn build
yarn lint
yarn lint:fix
yarn format:check
yarn type-check
yarn test
yarn test:coverage
```

Before committing frontend code, run:

```bash
yarn lint && yarn format:check && yarn type-check
```

Run `yarn test:coverage` when tests or tested behavior changed.

## App Structure

```text
frontend/src/
├── App.tsx                    # Router and top-level providers
├── main.tsx                   # ThemeProvider entrypoint
├── pages/                     # Route-level pages
├── components/
│   ├── ui/                    # Shadcn primitives and shared UI
│   ├── asset_dashboard/       # Dashboard charts/cards
│   ├── budget_dashboard/      # Budget page components
│   ├── transactions/          # Transaction table/forms/actions
│   ├── accounts/              # Account panels/forms
│   ├── settings/              # Preferences sections
│   └── household/             # Household controls such as ScopeToggle
├── contexts/                  # Auth, Household, Preferences, Theme, HeaderSlot
├── hooks/                     # useAuth, useBankAutomationStatus, useBankAutomationConnections, usePolling
├── lib/
│   ├── api/                   # API service singletons
│   ├── echarts.ts             # Tree-shaken ECharts exports
│   ├── format.ts              # Money/date helpers
│   └── utils.ts               # cn()
└── types/                     # UI/domain transform types
```

## Providers And Routing

Provider flow:

```text
ThemeProvider
  AuthProvider
    HouseholdProvider
      PreferencesProvider
        BrowserRouter
          ProtectedRoute
            Layout
              HeaderSlotProvider
```

Current protected routes:

| Path            | Page                                      |
| --------------- | ----------------------------------------- |
| `/dashboard`    | `ReportPage`                              |
| `/accounts`     | `Accounts`                                |
| `/bank-agent`   | `BankAgent`                               |
| `/budget`       | `BudgetDashboard` exported as `Dashboard` |
| `/transactions` | `DataTable`                               |
| `/setup`        | `Setup`                                   |
| `/preferences`  | `Preferences`                             |
| `/profile`      | `Profile`                                 |
| `/household`    | `HouseholdDashboard`                      |
| `/formulas`     | `Formulas`                                |
| `/more`         | `More`                                    |

Statement storage is configured from **Setup → Statements** (`/setup?tab=statements`) through the Google Drive statements section. `/upload` has been removed; statement records still use `frontend/src/lib/api/statementFiles.ts` for account-level recent file display and backend statement actions.

Redirects:

- `/` -> `/dashboard`
- `/cashflow` -> `/dashboard`
- `/settings` -> `/preferences`

When adding or renaming a route, update:

- `App.tsx`
- `components/Layout.tsx` `routeConfig`
- `components/Sidebar.tsx`
- `components/BottomTabBar.tsx` or `pages/More.tsx`

`/household` is conditional in the desktop sidebar based on `useHousehold().isInHousehold`.

## API Service Patterns

API code lives in `src/lib/api/` and exports singleton service instances. Use the shared clients instead of raw `fetch` in new work.

- `BaseApiClient` and `fetchWithAuth` are preferred for authenticated GET-style service clients.
- `csrfService.fetchWithCsrf()` is preferred for POST, PUT, PATCH, and DELETE.
- Requests must include cookies through the shared clients.
- `fetchWithAuth` dispatches session-expired behavior on `401`.
- API base URLs use `import.meta.env.VITE_API_BASE_URL || '/api/v1'`.

Example shape:

```typescript
class ExampleApi extends BaseApiClient {
  async getThings(): Promise<Thing[]> {
    return this.get<Thing[]>('/things/');
  }

  async updateThing(id: number, data: UpdateThing): Promise<Thing> {
    return csrfService.fetchWithCsrf(`${this.baseUrl}/things/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
}

export const exampleApi = new ExampleApi();
```

Existing older services may still contain raw `fetch`; do not copy that into new code.

## Household Scope

`HouseholdContext` exposes personal versus household scope. Household-aware pages should:

- Read `scope` from `useHousehold()`.
- Pass scope into API service methods.
- Omit the `scope` query parameter for personal views.
- Send `scope=household` only when household scope is selected.

The global `ScopeToggle` is rendered in `Layout`. Use `components/household/ScopeToggle.tsx` as the UI reference.

## State And Data Loading

- Use React Context for global auth, household, preferences, theme, date range, and header slot state.
- Use local `useState` for page UI such as modals, loading, and selected rows.
- Use URL search params for shareable table filters and page filters.
- Data fetching is generally `useEffect` plus API services; use `Promise.all` for independent parallel loads.
- Context hooks should throw when used outside their provider.

## Design System

- Use Tailwind utilities and `cn()` from `@/lib/utils`.
- Use Shadcn UI primitives from `components/ui/`.
- Use CSS variables and tokens such as `background`, `foreground`, `card`, `primary`, `muted`, `border`, and `destructive`.
- Avoid new hard-coded hex/rgb colors. Semantic Tailwind colors such as `emerald-500` for synced/positive states are acceptable where already established.
- Use `formatCurrency`, `formatSignedCurrency`, and preference helpers for money display.
- Use Lucide icons only.
- Use Sonner for toasts.

## Charts

- Import ECharts pieces from `@/lib/echarts`; do not import the whole `echarts` package in new code.
- Follow `components/asset_dashboard/BaseChart.tsx` for shared chart behavior.
- Read CSS variables with `getComputedStyle` or accept theme-aware colors via props.
- Always set an explicit chart height.
- Format money values in tooltips with project format helpers and preferences.

## Tables

Use the shared TanStack wrapper in `components/ui/DataTable.tsx`, `SortableHeader`, and column filter helpers. Keep API types in service files and UI transform types in `src/types/` when the display shape differs from the API shape.

## Responsive Navigation

- Desktop: `Sidebar` is `hidden md:flex`.
- Mobile: `BottomTabBar` is `md:hidden fixed bottom-0`.
- Main content includes bottom padding for mobile tab clearance.
- `pages/More.tsx` contains overflow mobile entries such as setup, preferences, formulas, profile, and logout.
- `MobileBottomNav.tsx` is legacy and should not be used for new navigation.

## Testing

Tests live under `frontend/tests/`. Use the custom render helpers in `tests/test-utils/` for router/context setup. API tests mock `global.fetch`; hook tests use wrapper factories when providers are required.

Run focused tests during development, then `yarn test:coverage` before committing tested behavior changes.
