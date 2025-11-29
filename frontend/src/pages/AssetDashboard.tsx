import { AccountDetailModal } from '@/components/asset_dashboard/AccountDetailModal';
import { AccountsSection } from '@/components/asset_dashboard/AccountsSection';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { SavingsChart } from '@/components/asset_dashboard/SavingsChart';
import { usePreferences } from '@/contexts/PreferencesContext';
import { assetDashboardApiService } from '@/lib/api/asset-dashboard';
import { formatCurrency } from '@/lib/format';
import { AlertTriangle, PiggyBank, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AssetDashboardData {
  networth: string | number;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  total_income: string | number;
  total_expenses: string | number;
}

export function AssetDashboard() {
  const { preferences } = usePreferences();
  const [dashboardData, setDashboardData] = useState<AssetDashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const stableSavingsChart = useMemo(() => <SavingsChart />, []);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<any | null>(null);
  const [accountsReloadKey, setAccountsReloadKey] = useState(0);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from asset dashboard API
      const dashboardMetrics =
        await assetDashboardApiService.getDashboardMetrics();

      setDashboardData({
        networth: dashboardMetrics.networth,
        networth_growth: dashboardMetrics.networth_growth,
        networth_growth_class: dashboardMetrics.networth_growth_class,
        savings_rate: dashboardMetrics.savings_rate,
        savings_rate_class: dashboardMetrics.savings_rate_class,
        savings_rate_context: dashboardMetrics.savings_rate_context,
        total_income: dashboardMetrics.income_sum,
        total_expenses: dashboardMetrics.expense_sum,
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

  const openAccountModal = (account: any) => {
    setSelectedAccount(account);
    setAccountModalOpen(true);
  };

  const handleAccountUpdated = () => {
    setAccountsReloadKey(v => v + 1);
    loadDashboardData();
  };

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
          value={formatCurrency(
            typeof dashboardData.networth === 'string'
              ? parseFloat(dashboardData.networth)
              : dashboardData.networth,
            preferences.currency,
            0
          )}
          subtitle={dashboardData.networth_growth}
          icon={<TrendingUp className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Net Worth = Sum of all account balances.
              </p>
              <p>
                Currently simplified to total assets across linked accounts.
              </p>
            </div>
          }
        />

        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          icon={<PiggyBank className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Savings Rate = (Income - Expenses) / Income.
              </p>
              <p>Income and expenses are summed over the selected period.</p>
            </div>
          }
        />

        {/* Removed Investment Performance card until backed by real data */}
      </div>

      {/* Main Asset Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-1 w-full min-w-0">
        {/* Savings Trend */}
        <div className="w-full overflow-x-auto">{stableSavingsChart}</div>

        {/* Accounts */}
        <div className="lg:col-span-2 w-full overflow-x-auto">
          <AccountsSection
            onAccountClick={openAccountModal}
            reloadKey={accountsReloadKey}
          />
        </div>
      </div>

      {/* Account Update Modal */}
      <AccountDetailModal
        account={selectedAccount}
        isOpen={accountModalOpen}
        onClose={() => setAccountModalOpen(false)}
        onAccountUpdated={handleAccountUpdated}
      />
    </div>
  );
}
