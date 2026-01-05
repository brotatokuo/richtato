import { AccountBreakdownChart } from '@/components/asset_dashboard/AccountBreakdownChart';
import {
  AccountGroup,
  AccountsList,
  AccountWithBalance,
} from '@/components/asset_dashboard/AccountsList';
import { AssetTrendsChart } from '@/components/asset_dashboard/AssetTrendsChart';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { assetDashboardApiService } from '@/lib/api/asset-dashboard';
import { formatCurrency } from '@/lib/format';
import { AlertTriangle, PiggyBank, TrendingUp, Wallet } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AssetDashboardData {
  networth: number;
  total_assets: number;
  total_liabilities: number;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  income_sum: number;
  expense_sum: number;
}

export function AssetDashboard() {
  const { preferences } = usePreferences();
  const [dashboardData, setDashboardData] = useState<AssetDashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAccount, setSelectedAccount] =
    useState<AccountWithBalance | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<AccountGroup | null>(null);
  const [accountsReloadKey, setAccountsReloadKey] = useState(0);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const dashboardMetrics =
        await assetDashboardApiService.getDashboardMetrics();

      setDashboardData({
        networth: dashboardMetrics.networth,
        total_assets: dashboardMetrics.total_assets,
        total_liabilities: dashboardMetrics.total_liabilities,
        networth_growth: dashboardMetrics.networth_growth,
        networth_growth_class: dashboardMetrics.networth_growth_class,
        savings_rate: dashboardMetrics.savings_rate,
        savings_rate_class: dashboardMetrics.savings_rate_class,
        savings_rate_context: dashboardMetrics.savings_rate_context,
        income_sum: dashboardMetrics.income_sum,
        expense_sum: dashboardMetrics.expense_sum,
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

  const handleAccountSelect = (account: AccountWithBalance | null) => {
    setSelectedAccount(account);
    if (account) {
      setSelectedGroup(null); // Clear group when selecting individual account
    }
  };

  const handleGroupSelect = (group: AccountGroup | null) => {
    setSelectedGroup(group);
    if (group) {
      setSelectedAccount(null); // Clear individual account when selecting group
    }
  };

  const handleResetSelection = () => {
    setSelectedAccount(null);
    setSelectedGroup(null);
  };

  const handleDataChange = () => {
    setAccountsReloadKey(v => v + 1);
    loadDashboardData();
  };

  if (loading && !dashboardData) {
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
      {/* Top KPI Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 w-full min-w-0">
        {/* Net Worth Card - Large with breakdown */}
        <div className="lg:col-span-2">
          <MetricCard
            title="Net Worth"
            value={formatCurrency(
              dashboardData.networth,
              preferences.currency,
              0
            )}
            subtitle={dashboardData.networth_growth}
            icon={<TrendingUp className="h-4 w-4" />}
            valueClassName={
              dashboardData.networth >= 0 ? 'text-green-500' : 'text-red-500'
            }
            info={
              <div className="space-y-2">
                <p className="text-foreground">
                  Net Worth = Total Assets - Total Liabilities
                </p>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Assets</p>
                    <p className="font-semibold text-green-500">
                      {formatCurrency(
                        dashboardData.total_assets,
                        preferences.currency,
                        0
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Liabilities</p>
                    <p className="font-semibold text-red-500">
                      {formatCurrency(
                        dashboardData.total_liabilities,
                        preferences.currency,
                        0
                      )}
                    </p>
                  </div>
                </div>
              </div>
            }
          >
            {/* Assets vs Liabilities breakdown bar */}
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">Assets</span>
                  <span className="font-medium text-green-500">
                    {formatCurrency(
                      dashboardData.total_assets,
                      preferences.currency,
                      0
                    )}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-red-500">
                    {formatCurrency(
                      dashboardData.total_liabilities,
                      preferences.currency,
                      0
                    )}
                  </span>
                  <span className="text-muted-foreground">Liabilities</span>
                </div>
              </div>
              {/* Visual bar */}
              <div className="h-2 bg-red-500/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${
                      dashboardData.total_assets +
                        dashboardData.total_liabilities >
                      0
                        ? (dashboardData.total_assets /
                            (dashboardData.total_assets +
                              dashboardData.total_liabilities)) *
                          100
                        : 50
                    }%`,
                  }}
                />
              </div>
            </div>
          </MetricCard>
        </div>

        {/* Savings Rate Card */}
        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          icon={<PiggyBank className="h-4 w-4" />}
          valueClassName={
            parseFloat(dashboardData.savings_rate) >= 20
              ? 'text-green-500'
              : parseFloat(dashboardData.savings_rate) >= 10
                ? 'text-yellow-500'
                : 'text-red-500'
          }
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Savings Rate = (Income - Expenses) / Income
              </p>
              <p className="text-sm text-muted-foreground">
                Based on the last 30 days of transactions.
              </p>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <p className="text-sm text-muted-foreground">Income</p>
                  <p className="font-semibold text-green-500">
                    {formatCurrency(
                      dashboardData.income_sum,
                      preferences.currency,
                      0
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Expenses</p>
                  <p className="font-semibold text-red-500">
                    {formatCurrency(
                      dashboardData.expense_sum,
                      preferences.currency,
                      0
                    )}
                  </p>
                </div>
              </div>
            </div>
          }
        />
      </div>

      {/* Asset Trends - unified chart */}
      <AssetTrendsChart
        selectedAccount={selectedAccount}
        selectedGroup={selectedGroup}
        onResetSelection={handleResetSelection}
        onDataChange={handleDataChange}
      />

      {/* Account Breakdown + Accounts List */}
      <div className="grid gap-6 lg:grid-cols-5 w-full min-w-0">
        {/* Account Breakdown Chart */}
        <div className="lg:col-span-2 min-w-0 w-full overflow-hidden">
          <AccountBreakdownChart />
        </div>

        {/* Accounts List */}
        <div className="lg:col-span-3 min-w-0">
          <AccountsList
            selectedAccountId={selectedAccount?.id ?? null}
            selectedGroupType={selectedGroup?.type ?? null}
            onAccountSelect={handleAccountSelect}
            onGroupSelect={handleGroupSelect}
            reloadKey={accountsReloadKey}
          />
        </div>
      </div>
    </div>
  );
}
