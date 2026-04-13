import { Dashboard } from '@/pages/BudgetDashboard';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { MultiMonthBudgetProgressData } from '@/lib/api/budget-dashboard';

vi.mock('@/components/asset_dashboard/BaseChart', () => ({
  BaseChart: () => <div data-testid="mock-chart">Chart</div>,
}));

const mockGetMultiMonth = vi.fn();

vi.mock('@/lib/api/budget-dashboard', () => ({
  budgetDashboardApiService: {
    getBudgetProgressMultiMonth: (...args: unknown[]) =>
      mockGetMultiMonth(...args),
    getExpenseCategoriesData: vi.fn().mockResolvedValue({
      labels: [],
      datasets: [{ data: [], backgroundColor: [] }],
    }),
  },
}));

vi.mock('@/contexts/PreferencesContext', () => ({
  usePreferences: () => ({
    preferences: {
      currency: 'USD',
      theme: 'system',
      date_format: 'MM/DD/YYYY',
      timezone: 'UTC',
    },
    currencySymbols: {},
    loading: false,
    error: null,
    refetch: vi.fn(),
    updatePreferences: vi.fn(),
    getCurrencySymbol: () => '$',
  }),
}));

vi.mock('@/lib/api/transactions', () => ({
  transactionsApiService: {
    getBudgetDashboard: vi.fn().mockResolvedValue({ budgets: [] }),
    getTransactions: vi.fn().mockResolvedValue({ results: [] }),
  },
}));

const mockMultiMonthData: MultiMonthBudgetProgressData = {
  monthly_data: [
    {
      year: 2024,
      month: 1,
      month_name: 'Jan',
      label: 'Jan 2024',
      total_budget: 2000,
      total_spent: 1500,
      total_remaining: 500,
      percentage: 75,
      categories: [
        {
          category: 'Food',
          budget: 1000,
          spent: 800,
          percentage: 80,
          remaining: 200,
        },
        {
          category: 'Transport',
          budget: 1000,
          spent: 700,
          percentage: 70,
          remaining: 300,
        },
      ],
      start_date: '2024-01-01',
      end_date: '2024-01-31',
    },
    {
      year: 2024,
      month: 2,
      month_name: 'Feb',
      label: 'Feb 2024',
      total_budget: 2000,
      total_spent: 2200,
      total_remaining: -200,
      percentage: 110,
      categories: [],
      start_date: '2024-02-01',
      end_date: '2024-02-29',
    },
  ],
  months_requested: 12,
};

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
}

beforeEach(() => {
  mockGetMultiMonth.mockReset();
});

describe('BudgetDashboard page', () => {
  it('calls getBudgetProgressMultiMonth with months=12 on mount', async () => {
    mockGetMultiMonth.mockResolvedValueOnce(mockMultiMonthData);

    renderDashboard();

    await waitFor(() => {
      expect(mockGetMultiMonth).toHaveBeenCalledWith({ months: 12 });
    });
  });

  it('renders KPI cards after loading', async () => {
    mockGetMultiMonth.mockResolvedValueOnce(mockMultiMonthData);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Current Month')).toBeInTheDocument();
    });

    expect(screen.getByText('12-Month Average')).toBeInTheDocument();
    expect(screen.getByText('Months Over Budget')).toBeInTheDocument();
    expect(screen.getByText('Months Tracked')).toBeInTheDocument();
  });

  it('shows correct current month utilization', async () => {
    mockGetMultiMonth.mockResolvedValueOnce(mockMultiMonthData);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('110%')).toBeInTheDocument();
    });
  });

  it('renders error state with retry button', async () => {
    mockGetMultiMonth.mockRejectedValueOnce(new Error('Network error'));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Error loading dashboard/)).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('renders month timeline section', async () => {
    mockGetMultiMonth.mockResolvedValueOnce(mockMultiMonthData);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Monthly Budget Timeline')).toBeInTheDocument();
    });
  });
});
