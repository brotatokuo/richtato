import { AccountDetailPanel } from '@/components/accounts/AccountDetailPanel';
import {
  AccountsSidebar,
  AccountWithBalance,
} from '@/components/accounts/AccountsSidebar';
import { AccountBreakdownChart } from '@/components/asset_dashboard/AccountBreakdownChart';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { NetWorthTrendChart } from '@/components/asset_dashboard/NetWorthTrendChart';
import { ConnectBankWizard } from '@/components/bank-sync/ConnectBankWizard';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { useBankSyncLogins } from '@/hooks/useBankSyncLogins';
import {
  AssetDashboardData,
  assetDashboardApiService,
} from '@/lib/api/asset-dashboard';
import { bankSyncApi } from '@/lib/api/bankSync';
import { formatCurrency, formatPeriodLabel } from '@/lib/format';
import {
  Link2,
  Loader2,
  PiggyBank,
  RefreshCw,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useMemo, useEffect, useState } from 'react';
import { toast } from 'sonner';

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
  const [showConnect, setShowConnect] = useState(false);
  const [syncingAll, setSyncingAll] = useState(false);

  const {
    logins,
    byAccount: syncMap,
    refresh: refreshLogins,
  } = useBankSyncLogins();

  const syncableLogins = useMemo(
    () => logins.filter(l => l.status === 'active'),
    [logins]
  );

  const handleAccountsChange = () => {
    setReloadKey(k => k + 1);
  };

  const handleAccountUpdated = () => {
    setReloadKey(k => k + 1);
  };

  const handleSyncChange = async () => {
    await refreshLogins();
  };

  const handleSyncAll = async () => {
    if (syncableLogins.length === 0) return;
    setSyncingAll(true);
    try {
      await Promise.allSettled(
        syncableLogins.map(l => bankSyncApi.syncNow(l.id))
      );
      toast.success('Sync queued for all bank logins', {
        description: `Queued ${syncableLogins.length} login${
          syncableLogins.length === 1 ? '' : 's'
        }. We'll run them on the next poll.`,
      });
      await refreshLogins();
    } catch (err) {
      toast.error('Failed to queue sync', {
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setSyncingAll(false);
    }
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

  const netCashFlow = dashboardData ? dashboardData.net_cashflow : 0;

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
              title={`Savings Rate (${formatPeriodLabel(dashboardData.period)})`}
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
              title={`Net Cash Flow (${formatPeriodLabel(dashboardData.period)})`}
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

      {/* Sync action header */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/40 bg-card/60 px-3 py-2">
        <div className="text-sm text-muted-foreground">
          {logins.length === 0
            ? 'No bank logins connected yet.'
            : `${logins.length} bank login${logins.length === 1 ? '' : 's'} connected • ${syncMap.size} account${syncMap.size === 1 ? '' : 's'} auto-synced`}
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowConnect(true)}
            className="h-8 gap-1.5 text-xs"
          >
            <Link2 className="h-3.5 w-3.5" />
            Connect bank
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleSyncAll}
            disabled={syncingAll || syncableLogins.length === 0}
            className="h-8 gap-1.5 text-xs"
          >
            {syncingAll ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            Sync all
          </Button>
        </div>
      </div>

      <div className="flex min-h-[36rem] h-[calc(100vh-32rem)] overflow-hidden rounded-lg border border-border/40 bg-card">
        {/* Left sidebar */}
        <div className="w-72 flex-shrink-0 border-r border-border/60 bg-card/80 overflow-hidden flex flex-col">
          <AccountsSidebar
            key={reloadKey}
            selectedAccountId={selectedAccount?.id ?? null}
            onAccountSelect={setSelectedAccount}
            onAccountsChange={handleAccountsChange}
            syncMap={syncMap}
          />
        </div>

        {/* Right detail panel */}
        <div className="flex-1 min-w-0 overflow-hidden bg-background">
          <AccountDetailPanel
            account={selectedAccount}
            sync={
              selectedAccount ? (syncMap.get(selectedAccount.id) ?? null) : null
            }
            onAccountUpdated={handleAccountUpdated}
            onSyncChange={handleSyncChange}
          />
        </div>
      </div>

      <ConnectBankWizard
        open={showConnect}
        onOpenChange={setShowConnect}
        onConnected={async () => {
          await refreshLogins();
        }}
      />
    </div>
  );
}
