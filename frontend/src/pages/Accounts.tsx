import { AccountDetailPanel } from '@/components/accounts/AccountDetailPanel';
import {
  AccountsSidebar,
  AccountWithBalance,
} from '@/components/accounts/AccountsSidebar';
import { AccountBreakdownChart } from '@/components/asset_dashboard/AccountBreakdownChart';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { NetWorthTrendChart } from '@/components/asset_dashboard/NetWorthTrendChart';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  AssetDashboardData,
  assetDashboardApiService,
} from '@/lib/api/asset-dashboard';
import { formatCurrency } from '@/lib/format';
import { PiggyBank, TrendingUp, Wallet } from 'lucide-react';
import { useEffect, useState } from 'react';

export function Accounts() {
  const { preferences } = usePreferences();
  const [selectedAccount, setSelectedAccount] =
    useState<AccountWithBalance | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [dashboardData, setDashboardData] = useState<AssetDashboardData | null>(
    null
  );
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  const handleAccountsChange = () => {
    setReloadKey(k => k + 1);
    // Clear selection if the selected account may have been deleted
  };

  const handleAccountUpdated = () => {
    setReloadKey(k => k + 1);
  };

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setMetricsLoading(true);
        setMetricsError(null);
        const dashboardMetrics =
          await assetDashboardApiService.getDashboardMetrics();
        setDashboardData(dashboardMetrics);
      } catch (err) {
        setMetricsError(
          err instanceof Error ? err.message : 'Failed to load account metrics'
        );
      } finally {
        setMetricsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const netCashFlow = dashboardData
    ? dashboardData.income_sum - dashboardData.expense_sum
    : 0;

  return (
    <div className="space-y-4">
      {metricsLoading && !dashboardData ? (
        <div className="flex items-center justify-center h-24 rounded-lg border border-border/40 bg-card/60">
          <LoadingSpinner />
        </div>
      ) : metricsError ? (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
          Account analytics are temporarily unavailable. You can still manage
          accounts normally.
        </div>
      ) : dashboardData ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="xl:col-span-2">
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
                  dashboardData.networth >= 0
                    ? 'text-green-500'
                    : 'text-red-500'
                }
              >
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

            <MetricCard
              title="Savings Rate (30d)"
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
            />

            <MetricCard
              title="Net Cash Flow (30d)"
              value={formatCurrency(netCashFlow, preferences.currency, 0)}
              subtitle={`Inflow ${formatCurrency(dashboardData.income_sum, preferences.currency, 0)} • Outflow ${formatCurrency(dashboardData.expense_sum, preferences.currency, 0)}`}
              icon={<Wallet className="h-4 w-4" />}
              valueClassName={
                netCashFlow >= 0 ? 'text-green-500' : 'text-red-500'
              }
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-5">
            <div className="xl:col-span-3">
              <NetWorthTrendChart />
            </div>
            <div className="xl:col-span-2">
              <AccountBreakdownChart />
            </div>
          </div>
        </>
      ) : null}

      <div className="flex min-h-[36rem] h-[calc(100vh-32rem)] overflow-hidden rounded-lg border border-border/40 bg-card">
        {/* Left sidebar */}
        <div className="w-72 flex-shrink-0 border-r border-border/60 bg-card/80 overflow-hidden flex flex-col">
          <AccountsSidebar
            key={reloadKey}
            selectedAccountId={selectedAccount?.id ?? null}
            onAccountSelect={setSelectedAccount}
            onAccountsChange={handleAccountsChange}
          />
        </div>

        {/* Right detail panel */}
        <div className="flex-1 min-w-0 overflow-hidden bg-background">
          <AccountDetailPanel
            account={selectedAccount}
            onAccountUpdated={handleAccountUpdated}
          />
        </div>
      </div>
    </div>
  );
}
