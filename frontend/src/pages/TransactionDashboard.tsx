import { IncomeExpenseChart } from '@/components/asset_dashboard/IncomeExpenseChart';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { BudgetProgress } from '@/components/budget_dashboard/BudgetProgress';
import { ExpenseBreakdown } from '@/components/budget_dashboard/ExpenseBreakdown';
import {
  BudgetDateRangeProvider,
  useBudgetDateRange,
} from '@/contexts/BudgetDateRangeContext';
import {
  CashFlowData,
  dashboardApiService,
  DashboardData,
} from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle, Gauge, Percent, PiggyBank } from 'lucide-react';
import { useEffect, useState } from 'react';

function DateRangeControls() {
  const { startDate, endDate, setRange } = useBudgetDateRange();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'start') setRange({ startDate: value, endDate });
    if (name === 'end') setRange({ startDate, endDate: value });
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        name="start"
        className="border rounded px-2 py-1 bg-background"
        value={startDate}
        onChange={handleChange}
      />
      <span className="text-muted-foreground">to</span>
      <input
        type="date"
        name="end"
        className="border rounded px-2 py-1 bg-background"
        value={endDate}
        onChange={handleChange}
      />
    </div>
  );
}

export function Dashboard() {
  return (
    <BudgetDateRangeProvider>
      <DashboardContent />
    </BudgetDateRangeProvider>
  );
}

function DashboardContent() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [incomeExpenseData, setIncomeExpenseData] =
    useState<CashFlowData | null>(null);
  const { startDate, endDate } = useBudgetDateRange();
  const [budgetUtilizationPct, setBudgetUtilizationPct] =
    useState<string>('N/A');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard metrics and income/expense data from the backend
      const [metricsData, incomeExpenseData] = await Promise.all([
        dashboardApiService.getDashboardMetrics(),
        dashboardApiService.getIncomeExpensesData(),
      ]);

      setDashboardData(metricsData);
      setIncomeExpenseData(incomeExpenseData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Recompute budget utilization when global date range changes
  useEffect(() => {
    const computeBudgetUtilization = async () => {
      try {
        const { budgets } = await transactionsApiService.getBudgetProgress({
          startDate,
          endDate,
        });
        const totalBudget = budgets.reduce(
          (sum: number, b: any) => sum + (b.budget || 0),
          0
        );
        const totalSpent = budgets.reduce(
          (sum: number, b: any) => sum + (b.spent || 0),
          0
        );
        const pct =
          totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;
        setBudgetUtilizationPct(`${pct}%`);
      } catch {
        setBudgetUtilizationPct('N/A');
      }
    };
    computeBudgetUtilization();
  }, [startDate, endDate]);

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading dashboard data...</div>
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
            onClick={loadDashboardData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <div className="space-y-6 max-w-full">
      {/* KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 min-w-0">
        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          icon={<PiggyBank className="h-4 w-4" />}
        />

        <MetricCard
          title="Budget Utilization"
          value={budgetUtilizationPct}
          subtitle="of selected period"
          icon={<Gauge className="h-4 w-4" />}
        />

        <MetricCard
          title="Non-Essential Spending"
          value={`${dashboardData.nonessential_spending_pct}%`}
          subtitle="of total spending"
          icon={<Percent className="h-4 w-4" />}
        />
      </div>

      {/* Global Budget Date Range Controls */}
      <div className="flex justify-end">
        <DateRangeControls />
      </div>

      {/* Budget Progress */}
      <div className="lg:col-span-2 min-w-0 overflow-x-auto">
        <BudgetProgress />
      </div>

      {/* Main Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-2 min-w-0">
        {/* Expense Breakdown */}
        <div className="lg:col-span-2 min-w-0 overflow-x-auto">
          <ExpenseBreakdown />
        </div>
        {/* Income vs Expenses Chart */}
        <div className="lg:col-span-2 min-w-0 overflow-x-auto">
          <IncomeExpenseChart data={incomeExpenseData} />
        </div>
      </div>
    </div>
  );
}
