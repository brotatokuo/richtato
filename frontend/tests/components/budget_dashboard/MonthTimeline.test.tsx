import { MonthTimeline } from '@/components/budget_dashboard/MonthTimeline';
import type { MonthlyBudgetData } from '@/lib/api/budget-dashboard';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/contexts/PreferencesContext', () => ({
  usePreferences: () => ({
    preferences: { currency: 'USD', theme: 'system', date_format: 'MM/DD/YYYY', timezone: 'UTC' },
    currencySymbols: {},
    loading: false,
    error: null,
    refetch: vi.fn(),
    updatePreferences: vi.fn(),
    getCurrencySymbol: () => '$',
  }),
}));

function makeMonth(overrides: Partial<MonthlyBudgetData> = {}): MonthlyBudgetData {
  return {
    year: 2024,
    month: 1,
    month_name: 'Jan',
    label: 'Jan 2024',
    total_budget: 1000,
    total_spent: 600,
    total_remaining: 400,
    percentage: 60,
    categories: [],
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    ...overrides,
  };
}

describe('MonthTimeline', () => {
  it('renders month cards from data', () => {
    const data = [
      makeMonth({ month: 1, month_name: 'Jan' }),
      makeMonth({ month: 2, month_name: 'Feb' }),
      makeMonth({ month: 3, month_name: 'Mar' }),
    ];

    render(<MonthTimeline monthlyData={data} onMonthClick={vi.fn()} />);

    expect(screen.getByText('Jan')).toBeInTheDocument();
    expect(screen.getByText('Feb')).toBeInTheDocument();
    expect(screen.getByText('Mar')).toBeInTheDocument();
  });

  it('shows over-budget percentage with red styling', () => {
    const data = [makeMonth({ percentage: 120, total_spent: 1200, total_remaining: -200 })];

    render(<MonthTimeline monthlyData={data} onMonthClick={vi.fn()} />);

    expect(screen.getByText('120% used')).toBeInTheDocument();
    expect(screen.getByText('Over')).toBeInTheDocument();
  });

  it('calls onMonthClick with correct data', () => {
    const onClick = vi.fn();
    const month = makeMonth({ month: 3, month_name: 'Mar' });

    render(<MonthTimeline monthlyData={[month]} onMonthClick={onClick} />);

    fireEvent.click(screen.getByText('Mar'));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onClick).toHaveBeenCalledWith(month);
  });

  it('shows "Viewing" badge on selected month', () => {
    const data = [
      makeMonth({ month: 1, month_name: 'Jan' }),
      makeMonth({ month: 2, month_name: 'Feb' }),
    ];

    render(
      <MonthTimeline
        monthlyData={data}
        onMonthClick={vi.fn()}
        selectedYear={2024}
        selectedMonth={2}
      />
    );

    expect(screen.getByText('Viewing')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<MonthTimeline monthlyData={[]} onMonthClick={vi.fn()} loading />);

    expect(screen.queryByText('Jan')).not.toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<MonthTimeline monthlyData={[]} onMonthClick={vi.fn()} />);

    expect(screen.getByText('No budget data available')).toBeInTheDocument();
  });
});
