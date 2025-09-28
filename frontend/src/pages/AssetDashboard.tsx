import { AccountsSection } from '@/components/dashboard/AccountsSection';
import { IncomeExpenseChart } from '@/components/dashboard/IncomeExpenseChart';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { SavingsChart } from '@/components/dashboard/SavingsChart';
import { dashboardApiService } from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import {
  AlertTriangle,
  Building2,
  PiggyBank,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface AssetDashboardData {
  networth: string;
  networth_growth: string;
  networth_growth_class: string;
  total_assets: string;
  total_liabilities: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  investment_performance: string;
  investment_performance_class: string;
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

      // Calculate total assets from accounts
      const totalAssets = accounts.reduce((sum, account) => {
        // Extract balance from account data
        const balance = account.balance || 0;
        return sum + balance;
      }, 0);

      // Calculate total income and expenses
      const totalIncome = incomeTransactions.reduce(
        (sum, transaction) => sum + transaction.amount,
        0
      );
      const totalExpenses = expenseTransactions.reduce(
        (sum, transaction) => sum + transaction.amount,
        0
      );

      // Calculate net worth (simplified as total assets for now)
      const netWorth = totalAssets;

      // Calculate investment performance (mock for now - would need historical data)
      const investmentPerformance = 0; // This would need historical data to calculate

      setDashboardData({
        networth: `$${netWorth.toLocaleString()}`,
        networth_growth: dashboardMetrics.networth_growth,
        networth_growth_class: dashboardMetrics.networth_growth_class,
        total_assets: `$${totalAssets.toLocaleString()}`,
        total_liabilities: '$0.00', // Would need liability data
        savings_rate: dashboardMetrics.savings_rate,
        savings_rate_class: dashboardMetrics.savings_rate_class,
        savings_rate_context: dashboardMetrics.savings_rate_context,
        investment_performance:
          investmentPerformance > 0
            ? `+${investmentPerformance.toFixed(1)}%`
            : `${investmentPerformance.toFixed(1)}%`,
        investment_performance_class:
          investmentPerformance >= 0 ? 'positive' : 'negative',
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
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading asset dashboard data...</span>
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
      {/* Asset KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Net Worth"
          value={dashboardData.networth}
          subtitle={dashboardData.networth_growth}
          trend={{
            value:
              dashboardData.networth_growth_class === 'positive' ? 2.1 : -1.2,
            label: 'vs last month',
          }}
          icon={<TrendingUp className="h-4 w-4" />}
        />

        <MetricCard
          title="Total Assets"
          value={dashboardData.total_assets}
          subtitle="All accounts combined"
          icon={<Building2 className="h-4 w-4" />}
        />

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
          title="Investment Performance"
          value={dashboardData.investment_performance}
          subtitle="YTD portfolio return"
          trend={{
            value: parseFloat(
              dashboardData.investment_performance.replace(/[+%]/g, '')
            ),
            label: 'vs market',
          }}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      {/* Main Asset Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Income vs Expenses */}
        <div>
          <IncomeExpenseChart />
        </div>

        {/* Savings Trend */}
        <div>
          <SavingsChart />
        </div>

        {/* Accounts */}
        <div className="lg:col-span-2">
          <AccountsSection />
        </div>
      </div>
    </div>
  );
}
