import { AccountsSection } from '@/components/asset_dashboard/AccountsSection';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { SavingsChart } from '@/components/asset_dashboard/SavingsChart';
import { dashboardApiService } from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle, PiggyBank, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AssetDashboardData {
  networth: string;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  total_income: string;
  total_expenses: string;
}

export function AssetDashboard() {
  const [dashboardData, setDashboardData] = useState<AssetDashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from multiple APIs
      const [
        dashboardMetrics,
        accounts,
        incomeTransactions,
        expenseTransactions,
      ] = await Promise.all([
        dashboardApiService.getDashboardMetrics(),
        transactionsApiService.getAccounts(),
        transactionsApiService.getIncomeTransactions(),
        transactionsApiService.getExpenseTransactions(),
      ]);

      // Helper to coerce currency strings or numbers to a number
      const parseAmountToNumber = (value: unknown): number => {
        if (typeof value === 'number') return value;
        if (typeof value === 'string') {
          const normalized = value.replace(/[^0-9.-]+/g, '');
          const parsed = parseFloat(normalized);
          return isNaN(parsed) ? 0 : parsed;
        }
        if (typeof value === 'bigint') return Number(value);
        return 0;
      };

      // Calculate total assets from accounts
      const totalAssets = accounts.reduce((sum, account) => {
        const balanceNumber = parseAmountToNumber((account as any).balance);
        return sum + balanceNumber;
      }, 0);

      // Calculate total income and expenses
      const totalIncome = incomeTransactions.reduce(
        (sum, transaction) =>
          sum + parseAmountToNumber((transaction as any).amount),
        0
      );
      const totalExpenses = expenseTransactions.reduce(
        (sum, transaction) =>
          sum + parseAmountToNumber((transaction as any).amount),
        0
      );

      // Calculate net worth (simplified as total assets for now)
      const netWorth = totalAssets;

      setDashboardData({
        networth: `$${netWorth.toLocaleString()}`,
        networth_growth: dashboardMetrics.networth_growth,
        networth_growth_class: dashboardMetrics.networth_growth_class,
        savings_rate: dashboardMetrics.savings_rate,
        savings_rate_class: dashboardMetrics.savings_rate_class,
        savings_rate_context: dashboardMetrics.savings_rate_context,
        total_income: `$${totalIncome.toLocaleString()}`,
        total_expenses: `$${totalExpenses.toLocaleString()}`,
      });
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
        <div className="text-muted-foreground">
          Loading asset dashboard data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600 mb-4">
            Error loading asset dashboard: {error}
          </p>
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
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Asset KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 w-full min-w-0">
        <MetricCard
          title="Net Worth"
          value={dashboardData.networth}
          subtitle={dashboardData.networth_growth}
          icon={<TrendingUp className="h-4 w-4" />}
        />

        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          icon={<PiggyBank className="h-4 w-4" />}
        />

        {/* Removed Investment Performance card until backed by real data */}
      </div>

      {/* Main Asset Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-1 w-full min-w-0">
        {/* Savings Trend */}
        <div className="w-full overflow-x-auto">
          <SavingsChart />
        </div>

        {/* Accounts */}
        <div className="lg:col-span-2 w-full overflow-x-auto">
          <AccountsSection />
        </div>
      </div>
    </div>
  );
}
