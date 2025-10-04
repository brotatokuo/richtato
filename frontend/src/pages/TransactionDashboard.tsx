import { BudgetProgress } from '@/components/dashboard/BudgetProgress';
import { ExpenseBreakdown } from '@/components/dashboard/ExpenseBreakdown';
import { IncomeExpenseChart } from '@/components/dashboard/IncomeExpenseChart';
import { MetricCard } from '@/components/dashboard/MetricCard';
import {
  CashFlowData,
  dashboardApiService,
  DashboardData,
} from '@/lib/api/dashboard';
import {
  AlertTriangle,
  Gauge,
  Percent,
  PiggyBank,
  TrendingUp,
} from 'lucide-react';
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
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
    <div className="space-y-6">
      {/* KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          trend={{
            value: dashboardData.savings_rate_class === 'positive' ? 1.2 : -0.5,
            label: 'vs last month',
          }}
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
      <div className="lg:col-span-2">
        <BudgetProgress />
      </div>

      {/* Main Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Income vs Expenses Chart */}
        <div className="lg:col-span-2">
          <IncomeExpenseChart data={incomeExpenseData} />
        </div>

        {/* Expense Breakdown */}
        <div className="lg:col-span-2">
          <ExpenseBreakdown />
        </div>
      </div>
    </div>
  );
}
