import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

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

const mockGetCatalog = vi.fn();
const mockGetBudgetDashboard = vi.fn();
const mockUpdateSettings = vi.fn();

vi.mock('@/lib/api/user', () => ({
  categorySettingsApi: {
    getCatalog: (...args: unknown[]) => mockGetCatalog(...args),
    updateSettings: (...args: unknown[]) => mockUpdateSettings(...args),
  },
}));

vi.mock('@/lib/api/transactions', () => ({
  transactionsApiService: {
    getBudgetDashboard: (...args: unknown[]) => mockGetBudgetDashboard(...args),
  },
}));

const mockCatalog = {
  categories: [
    {
      name: 'groceries',
      display: 'Groceries',
      type: 'expense',
      icon: '🛒',
      color: '#green',
      budget: {
        id: 1,
        amount: 500,
        start_date: '2024-01-01',
        end_date: '2024-01-31',
      },
    },
    {
      name: 'entertainment',
      display: 'Entertainment',
      type: 'expense',
      icon: '🎬',
      color: '#blue',
      budget: null,
    },
    {
      name: 'salary',
      display: 'Salary',
      type: 'income',
      icon: '💰',
      color: '#gold',
      budget: null,
    },
  ],
};

const mockProgress = {
  budgets: [
    {
      category: 'Groceries',
      budget: 500,
      spent: 300,
      percentage: 60,
      remaining: 200,
    },
  ],
};

function renderSection() {
  return render(
    <MemoryRouter>
      <BudgetsSection />
    </MemoryRouter>
  );
}

beforeEach(() => {
  mockGetCatalog.mockReset().mockResolvedValue(mockCatalog);
  mockGetBudgetDashboard.mockReset().mockResolvedValue(mockProgress);
  mockUpdateSettings.mockReset().mockResolvedValue({});
});

describe('BudgetsSection', () => {
  it('renders expense category cards with budget amounts', async () => {
    renderSection();

    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeInTheDocument();
    });

    expect(screen.getByText('$500.00')).toBeInTheDocument();
    expect(screen.getByText('Entertainment')).toBeInTheDocument();
    expect(screen.getByText('No budget')).toBeInTheDocument();
  });

  it('excludes non-expense categories', async () => {
    renderSection();

    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeInTheDocument();
    });

    expect(screen.queryByText('Salary')).not.toBeInTheDocument();
  });

  it('renders Monthly Budgets title', async () => {
    renderSection();

    await waitFor(() => {
      expect(screen.getByText('Monthly Budgets')).toBeInTheDocument();
    });
  });

  it('opens modal when card is clicked', async () => {
    renderSection();

    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Groceries'));

    await waitFor(() => {
      expect(screen.getByText('Edit Budget')).toBeInTheDocument();
    });

    expect(screen.getByText('Save Budget')).toBeInTheDocument();
    expect(screen.getByText('Remove Budget')).toBeInTheDocument();
  });
});
