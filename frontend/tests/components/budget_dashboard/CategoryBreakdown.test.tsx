import { CategoryBreakdown } from '@/components/budget_dashboard/CategoryBreakdown';
import { render, screen } from '@testing-library/react';

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

const categories = [
  {
    name: 'Groceries',
    budget: 500,
    spent: 300,
    percentage: 60,
    color: '#3b82f6',
    remaining: 200,
  },
  {
    name: 'Transport',
    budget: 200,
    spent: 250,
    percentage: 125,
    color: '#ef4444',
    remaining: -50,
  },
  {
    name: 'Entertainment',
    budget: 100,
    spent: 90,
    percentage: 90,
    color: '#f59e0b',
    remaining: 10,
  },
];

describe('CategoryBreakdown', () => {
  it('renders category names', () => {
    render(<CategoryBreakdown categories={categories} />);

    expect(screen.getByText('Groceries')).toBeInTheDocument();
    expect(screen.getByText('Transport')).toBeInTheDocument();
    expect(screen.getByText('Entertainment')).toBeInTheDocument();
  });

  it('shows "left" label for under-budget categories', () => {
    render(<CategoryBreakdown categories={categories} />);

    expect(screen.getByText('$200.00 left')).toBeInTheDocument();
  });

  it('shows "Over" label for over-budget categories', () => {
    render(<CategoryBreakdown categories={categories} />);

    expect(screen.getByText(/Over \$50\.00/)).toBeInTheDocument();
  });

  it('renders percentage for each category', () => {
    render(<CategoryBreakdown categories={categories} />);

    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('125%')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
  });
});
