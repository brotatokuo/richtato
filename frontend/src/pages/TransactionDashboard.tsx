import { BudgetProgress } from '@/components/dashboard/BudgetProgress';
import { ExpenseBreakdown } from '@/components/dashboard/ExpenseBreakdown';
import { IncomeExpenseChart } from '@/components/dashboard/IncomeExpenseChart';
import { MetricCard } from '@/components/dashboard/MetricCard';
import {
  CashFlowData,
  dashboardApiService,
  DashboardData,
} from '@/lib/api/dashboard';
import { AlertTriangle, Gauge, Percent, PiggyBank } from 'lucide-react';
import { useEffect, useState } from 'react';

export function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [incomeExpenseData, setIncomeExpenseData] =
    useState<CashFlowData | null>(null);
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
          value={dashboardData.budget_utilization_30_days}
          subtitle="of current month's budget"
          icon={<Gauge className="h-4 w-4" />}
        />

        <MetricCard
          title="Non-Essential Spending"
          value={`${dashboardData.nonessential_spending_pct}%`}
          subtitle="of total spending"
          icon={<Percent className="h-4 w-4" />}
        />
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
