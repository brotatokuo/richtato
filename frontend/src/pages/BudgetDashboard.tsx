import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { BudgetDashboard as BudgetBreakdownChart } from '@/components/budget_dashboard/BudgetBreakdown';
import { BudgetTrendsChart } from '@/components/budget_dashboard/BudgetTrendsChart';
import { ExpenseBreakdown } from '@/components/budget_dashboard/ExpenseBreakdown';
import { ExpenseDetailModal } from '@/components/budget_dashboard/ExpenseDetailModal';
import { MonthTimeline } from '@/components/budget_dashboard/MonthTimeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import {
  BudgetDateRangeProvider,
  useBudgetDateRange,
} from '@/contexts/BudgetDateRangeContext';
import {
  budgetDashboardApiService,
  type MonthlyBudgetData,
} from '@/lib/api/budget-dashboard';
import {
  AlertTriangle,
  CalendarDays,
  Gauge,
  Pencil,
  Percent,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export function Dashboard() {
  return (
    <BudgetDateRangeProvider>
      <DashboardContent />
    </BudgetDateRangeProvider>
  );
}

function DashboardContent() {
  const { setRange } = useBudgetDateRange();
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

  // Year and month state for the picker
  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);

  // Calculate aggregate KPIs from monthly data
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
    const fetchKey = 'multi-month-12';
    if (lastFetchRef.current === fetchKey) return;
    lastFetchRef.current = fetchKey;

    try {
      setLoading(true);
      setError(null);

      const multiMonthData =
        await budgetDashboardApiService.getBudgetProgressMultiMonth({
          months: 12,
        });

      setMonthlyData(multiMonthData.monthly_data);

      // Set the date range context to current month for expense breakdown
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
  }, [setRange]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleMonthClick = (month: MonthlyBudgetData) => {
    setSelectedMonth(month);
    setDisplayedMonth(month);
    setIsModalOpen(true);
    // Update date range context for expense breakdown
    setRange({
      startDate: month.start_date,
      endDate: month.end_date,
    });
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedMonth(null);
  };

  // Handle year/month change from picker
  const handleDateChange = (newYear: number, newMonth: number) => {
    setYear(newYear);
    setMonth(newMonth);

    // Find the corresponding month in our data
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

  // Sync picker state when displayedMonth changes (e.g., from timeline click)
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

  // Convert displayedMonth categories to the format expected by BudgetBreakdownChart
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

  return (
    <div className="space-y-6 w-full max-w-full overflow-hidden">
      {/* Month/Year Picker + Edit Budgets shortcut */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <MonthYearPicker
          year={year}
          month={month}
          onChange={handleDateChange}
        />
        <Link
          to="/setup?tab=budgets"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <Pencil className="h-3.5 w-3.5" />
          Edit Budgets
        </Link>
      </div>

      {/* Selected Month Budget Breakdown - At the Top */}
      <div className="w-full min-w-0">
        <BudgetBreakdownChart progress={budgetProgress} />
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

      {/* Expense Breakdown - shows data for selected/current month */}
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
