import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { BudgetDashboard as BudgetBreakdownChart } from '@/components/budget_dashboard/BudgetBreakdown';
import { BudgetTrendsChart } from '@/components/budget_dashboard/BudgetTrendsChart';
import { ExpenseBreakdown } from '@/components/budget_dashboard/ExpenseBreakdown';
import { ExpenseDetailModal } from '@/components/budget_dashboard/ExpenseDetailModal';
import { MonthTimeline } from '@/components/budget_dashboard/MonthTimeline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import {
  BudgetDateRangeProvider,
  useBudgetDateRange,
} from '@/contexts/BudgetDateRangeContext';
import { useHousehold } from '@/contexts/HouseholdContext';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  budgetDashboardApiService,
  type MonthlyBudgetData,
} from '@/lib/api/budget-dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { categorySettingsApi } from '@/lib/api/user';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  ArrowDown,
  ArrowUpDown,
  CalendarDays,
  DollarSign,
  Gauge,
  Pencil,
  Percent,
  PiggyBank,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

type SortOption = 'default' | 'over-first' | 'name' | 'spent';

export function Dashboard() {
  return (
    <BudgetDateRangeProvider>
      <DashboardContent />
    </BudgetDateRangeProvider>
  );
}

function DashboardContent() {
  const { setRange } = useBudgetDateRange();
  const { preferences } = usePreferences();
  const { scope } = useHousehold();
  const [monthlyData, setMonthlyData] = useState<MonthlyBudgetData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<MonthlyBudgetData | null>(
    null
  );
  const [displayedMonth, setDisplayedMonth] =
    useState<MonthlyBudgetData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const lastFetchRef = useRef<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('default');
  const [monthlyIncome, setMonthlyIncome] = useState<number>(0);

  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);

  const currentMonthData =
    monthlyData.length > 0 ? monthlyData[monthlyData.length - 1] : null;

  const aggregateStats = {
    averageUtilization:
      monthlyData.length > 0
        ? Math.round(
            monthlyData.reduce((sum, m) => sum + m.percentage, 0) /
              monthlyData.length
          )
        : 0,
    monthsOverBudget: monthlyData.filter(m => m.percentage > 100).length,
    currentUtilization: currentMonthData?.percentage ?? 0,
  };

  const loadDashboardData = useCallback(async () => {
    const fetchKey = `multi-month-12-${scope}`;
    if (lastFetchRef.current === fetchKey) return;
    lastFetchRef.current = fetchKey;

    try {
      setLoading(true);
      setError(null);

      const multiMonthData =
        await budgetDashboardApiService.getBudgetProgressMultiMonth({
          months: 12,
          scope,
        });

      setMonthlyData(multiMonthData.monthly_data);

      if (multiMonthData.monthly_data.length > 0) {
        const current =
          multiMonthData.monthly_data[multiMonthData.monthly_data.length - 1];
        setDisplayedMonth(current);
        setRange({
          startDate: current.start_date,
          endDate: current.end_date,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [setRange, scope]);

  // Fetch income for the displayed month
  useEffect(() => {
    if (!displayedMonth) return;
    transactionsApiService
      .getTransactions({
        startDate: displayedMonth.start_date,
        endDate: displayedMonth.end_date,
        type: 'credit',
        scope,
      })
      .then(({ transactions }) => {
        const income = transactions.reduce((sum, t) => sum + t.amount, 0);
        setMonthlyIncome(income);
      })
      .catch(() => setMonthlyIncome(0));
  }, [displayedMonth, scope]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleMonthClick = (month: MonthlyBudgetData) => {
    setSelectedMonth(month);
    setDisplayedMonth(month);
    setIsModalOpen(true);
    setRange({
      startDate: month.start_date,
      endDate: month.end_date,
    });
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedMonth(null);
  };

  const handleDateChange = (newYear: number, newMonth: number) => {
    setYear(newYear);
    setMonth(newMonth);

    const found = monthlyData.find(
      m => m.year === newYear && m.month === newMonth
    );

    if (found) {
      setDisplayedMonth(found);
      setRange({
        startDate: found.start_date,
        endDate: found.end_date,
      });
    }
  };

  const handleEditBudget = async (categoryName: string, newAmount: number) => {
    const catalogRes = await categorySettingsApi.getCatalog();
    const cat = catalogRes.categories.find(
      c =>
        c.display === categoryName ||
        c.name === categoryName.toLowerCase().replace(/\s+/g, '-')
    );
    if (!cat) return;

    await categorySettingsApi.updateSettings({
      enabled: catalogRes.categories.map(c => c.name),
      disabled: [],
      budgets: {
        [cat.name]: {
          amount: newAmount,
          start_date:
            displayedMonth?.start_date ??
            new Date(new Date().getFullYear(), new Date().getMonth(), 1)
              .toISOString()
              .slice(0, 10),
          end_date: null,
        },
      },
    });

    // Refresh data
    lastFetchRef.current = null;
    await loadDashboardData();
  };

  useEffect(() => {
    if (displayedMonth) {
      setYear(displayedMonth.year);
      setMonth(displayedMonth.month);
    }
  }, [displayedMonth]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600 mb-4">Error loading dashboard: {error}</p>
          <button
            onClick={() => {
              lastFetchRef.current = null;
              loadDashboardData();
            }}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (monthlyData.length === 0) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center max-w-md space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <PiggyBank className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            No budgets set up yet
          </h2>
          <p className="text-muted-foreground">
            Create budgets for your expense categories to start tracking your
            spending. You&apos;ll see progress charts, trends, and alerts here.
          </p>
          <Link to="/setup?tab=budgets">
            <Button className="mt-2">
              <PiggyBank className="h-4 w-4 mr-2" />
              Set Up Budgets
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const budgetProgress = displayedMonth
    ? displayedMonth.categories.map(cat => ({
        category: cat.category,
        budget: cat.budget,
        spent: cat.spent,
        percentage: cat.percentage,
        remaining: cat.remaining,
        year: displayedMonth.year,
        month: displayedMonth.month,
      }))
    : [];

  const totalBudget = displayedMonth?.total_budget ?? 0;
  const totalSpent = displayedMonth?.total_spent ?? 0;
  const leftToBudget = monthlyIncome - totalBudget;

  // Budget alerts
  const overBudgetCategories = displayedMonth
    ? displayedMonth.categories.filter(c => c.percentage > 100)
    : [];
  const warningCategories = displayedMonth
    ? displayedMonth.categories.filter(
        c => c.percentage > 80 && c.percentage <= 100
      )
    : [];

  // Spending projection
  const daysInMonth = displayedMonth
    ? new Date(displayedMonth.year, displayedMonth.month, 0).getDate()
    : 30;
  const currentDay = Math.min(now.getDate(), daysInMonth);
  const isCurrentMonth =
    displayedMonth?.year === now.getFullYear() &&
    displayedMonth?.month === now.getMonth() + 1;
  const projectedSpend =
    isCurrentMonth && currentDay > 0
      ? Math.round((totalSpent / currentDay) * daysInMonth)
      : totalSpent;

  const sortOptions: { value: SortOption; label: string }[] = [
    { value: 'default', label: 'Default' },
    { value: 'over-first', label: 'Over budget first' },
    { value: 'name', label: 'Name A-Z' },
    { value: 'spent', label: 'Most spent' },
  ];

  return (
    <div className="space-y-6 w-full max-w-full overflow-hidden">
      {/* Header row */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <MonthYearPicker
          year={year}
          month={month}
          onChange={handleDateChange}
        />
        <div className="flex items-center gap-3">
          {/* Sort dropdown */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as SortOption)}
              className="appearance-none text-sm bg-transparent border border-border rounded-md px-3 py-1.5 pr-7 text-muted-foreground hover:text-foreground cursor-pointer transition-colors"
            >
              {sortOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <ArrowUpDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
          </div>
          <Link
            to="/setup?tab=budgets"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit Budgets
          </Link>
        </div>
      </div>

      {/* Budget alerts banner */}
      {(overBudgetCategories.length > 0 || warningCategories.length > 0) && (
        <div
          className={cn(
            'rounded-lg border p-3 text-sm flex items-start gap-2',
            overBudgetCategories.length > 0
              ? 'border-destructive/50 bg-destructive/5 text-destructive'
              : 'border-amber-500/50 bg-amber-500/5 text-amber-700 dark:text-amber-400'
          )}
        >
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div>
            {overBudgetCategories.length > 0 && (
              <span className="font-medium">
                {overBudgetCategories.length}{' '}
                {overBudgetCategories.length === 1
                  ? 'category is'
                  : 'categories are'}{' '}
                over budget
                {overBudgetCategories.length <= 3 &&
                  `: ${overBudgetCategories.map(c => c.category).join(', ')}`}
                .{' '}
              </span>
            )}
            {warningCategories.length > 0 && (
              <span>
                {warningCategories.length} approaching limit (&gt;80%).
              </span>
            )}
          </div>
        </div>
      )}

      {/* Income context bar */}
      <Card>
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between flex-wrap gap-x-6 gap-y-2 text-sm">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-500" />
              <span className="text-muted-foreground">Income</span>
              <span className="font-semibold text-foreground">
                {formatCurrency(monthlyIncome, preferences.currency)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowDown className="h-4 w-4 text-blue-500" />
              <span className="text-muted-foreground">Budgeted</span>
              <span className="font-semibold text-foreground">
                {formatCurrency(totalBudget, preferences.currency)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <PiggyBank className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Left to budget</span>
              <span
                className={cn(
                  'font-semibold',
                  leftToBudget < 0 ? 'text-destructive' : 'text-emerald-600'
                )}
              >
                {formatCurrency(leftToBudget, preferences.currency)}
              </span>
            </div>
            {isCurrentMonth && (
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-amber-500" />
                <span className="text-muted-foreground">Projected spend</span>
                <span
                  className={cn(
                    'font-semibold',
                    projectedSpend > totalBudget
                      ? 'text-destructive'
                      : 'text-foreground'
                  )}
                >
                  {formatCurrency(projectedSpend, preferences.currency)}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Budget Breakdown with inline editing */}
      <div className="w-full min-w-0">
        <BudgetBreakdownChart
          progress={budgetProgress}
          onEditBudget={handleEditBudget}
          sortBy={sortBy}
        />
      </div>

      {/* Month Timeline */}
      <div className="flex w-full">
        <div className="flex-1 min-w-0">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <CalendarDays className="h-5 w-5" />
                Monthly Budget Timeline
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Click on any month to view detailed expenses and update the
                budget breakdown above
              </p>
            </CardHeader>
            <CardContent className="px-2 sm:px-6 min-w-0">
              <div className="w-full min-w-0">
                <MonthTimeline
                  monthlyData={monthlyData}
                  onMonthClick={handleMonthClick}
                  loading={loading}
                  selectedYear={displayedMonth?.year}
                  selectedMonth={displayedMonth?.month}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* KPI Summary Row */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 w-full min-w-0">
        <MetricCard
          title="Current Month"
          value={`${aggregateStats.currentUtilization}%`}
          subtitle={currentMonthData?.label ?? 'N/A'}
          icon={<Gauge className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Budget utilization for the current month.
              </p>
              <p>Shows how much of this month&apos;s budget has been used.</p>
            </div>
          }
        />

        <MetricCard
          title="12-Month Average"
          value={`${aggregateStats.averageUtilization}%`}
          subtitle="average utilization"
          icon={<Percent className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Average budget utilization over the last 12 months.
              </p>
              <p>A lower average indicates better budget discipline.</p>
            </div>
          }
        />

        <MetricCard
          title="Months Over Budget"
          value={String(aggregateStats.monthsOverBudget)}
          subtitle="in the last 12 months"
          icon={<TrendingUp className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Number of months where spending exceeded the budget.
              </p>
              <p>Aim to keep this number as low as possible.</p>
            </div>
          }
        />

        <MetricCard
          title="Months Tracked"
          value={String(monthlyData.length)}
          subtitle="with budget data"
          icon={<CalendarDays className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Total months with budget tracking data.
              </p>
              <p>Click on any month in the timeline to view details.</p>
            </div>
          }
        />
      </div>

      {/* Budget Trends Chart */}
      <div className="w-full min-w-0">
        <BudgetTrendsChart monthlyData={monthlyData} loading={loading} />
      </div>

      {/* Expense Breakdown */}
      <div className="w-full min-w-0">
        <ExpenseBreakdown />
      </div>

      {/* Expense Detail Modal */}
      <ExpenseDetailModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        monthData={selectedMonth}
      />
    </div>
  );
}
