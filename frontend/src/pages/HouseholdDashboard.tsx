import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useHousehold } from '@/contexts/HouseholdContext';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  AssetDashboardData,
  assetDashboardApiService,
} from '@/lib/api/asset-dashboard';
import {
  Account,
  Transaction,
  transactionsApiService,
} from '@/lib/api/transactions';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';
import {
  ArrowRight,
  CreditCard,
  Heart,
  Landmark,
  PiggyBank,
  TrendingUp,
  UserPlus,
  Users,
  Wallet,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';

export function HouseholdDashboard() {
  const {
    household,
    isInHousehold,
    isLoading: householdLoading,
    members,
    partnerName,
  } = useHousehold();
  const { preferences } = usePreferences();

  const [metrics, setMetrics] = useState<AssetDashboardData | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [metricsData, accountsData, txnData] = await Promise.all([
        assetDashboardApiService.getDashboardMetrics({ scope: 'household' }),
        transactionsApiService.getAccounts({ scope: 'household' }),
        transactionsApiService.getTransactions({
          scope: 'household',
          pageSize: 10,
        }),
      ]);
      setMetrics(metricsData);
      setAccounts(accountsData);
      setTransactions(txnData.transactions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isInHousehold) {
      loadData();
    }
  }, [isInHousehold, loadData]);

  if (householdLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isInHousehold) {
    return <Navigate to="/setup?tab=household" replace />;
  }

  const netCashFlow = metrics ? metrics.income_sum - metrics.expense_sum : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Heart className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{household?.name}</h1>
            <p className="text-sm text-muted-foreground">
              {partnerName ? `You & ${partnerName}` : 'Household Overview'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {members.length < 2 && (
            <Link
              to="/setup?tab=household"
              className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Invite Partner
            </Link>
          )}
          <Link
            to="/setup?tab=household"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Settings
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Members */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {members.map(m => (
          <Card key={m.user_id} className="bg-card/50 border-border/50">
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                {m.username.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{m.username}</p>
                <p className="text-xs text-muted-foreground">
                  Joined {new Date(m.joined_at).toLocaleDateString()}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="flex items-center justify-center p-8 text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Metrics */}
          {metrics && (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="xl:col-span-2">
                <MetricCard
                  title="Combined Net Worth"
                  value={formatCurrency(
                    metrics.networth,
                    preferences.currency,
                    0
                  )}
                  icon={<TrendingUp className="h-4 w-4" />}
                  valueClassName={
                    metrics.networth >= 0 ? 'text-green-500' : 'text-red-500'
                  }
                >
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Wallet className="h-4 w-4 text-green-500" />
                        <span className="text-muted-foreground">
                          Shared Assets
                        </span>
                        <span className="font-medium text-green-500">
                          {formatCurrency(
                            metrics.total_assets,
                            preferences.currency,
                            0
                          )}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-red-500">
                          {formatCurrency(
                            metrics.total_liabilities,
                            preferences.currency,
                            0
                          )}
                        </span>
                        <span className="text-muted-foreground">
                          Liabilities
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-red-500/20 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all duration-500"
                        style={{
                          width: `${
                            metrics.total_assets + metrics.total_liabilities > 0
                              ? (metrics.total_assets /
                                  (metrics.total_assets +
                                    metrics.total_liabilities)) *
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
                value={metrics.savings_rate}
                subtitle={metrics.savings_rate_context}
                icon={<PiggyBank className="h-4 w-4" />}
                valueClassName={
                  parseFloat(metrics.savings_rate) >= 20
                    ? 'text-green-500'
                    : parseFloat(metrics.savings_rate) >= 10
                      ? 'text-yellow-500'
                      : 'text-red-500'
                }
              />

              <MetricCard
                title="Net Cash Flow (30d)"
                value={formatCurrency(netCashFlow, preferences.currency, 0)}
                subtitle={`In ${formatCurrency(metrics.income_sum, preferences.currency, 0)} · Out ${formatCurrency(metrics.expense_sum, preferences.currency, 0)}`}
                icon={<Wallet className="h-4 w-4" />}
                valueClassName={
                  netCashFlow >= 0 ? 'text-green-500' : 'text-red-500'
                }
              />
            </div>
          )}

          {/* Shared Accounts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Landmark className="h-5 w-5" />
                Shared Accounts
                <span className="ml-auto text-sm font-normal text-muted-foreground">
                  {accounts.length} account{accounts.length !== 1 ? 's' : ''}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {accounts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <CreditCard className="h-8 w-8 text-muted-foreground/50 mb-2" />
                  <p className="text-sm text-muted-foreground">
                    No shared accounts yet. Mark accounts as shared in the{' '}
                    <Link
                      to="/accounts"
                      className="text-primary hover:underline"
                    >
                      Accounts page
                    </Link>
                    .
                  </p>
                </div>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {accounts.map(account => (
                    <div
                      key={account.id}
                      className="flex items-center gap-3 rounded-lg border border-border/60 p-3 hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted">
                        {account.account_type === 'credit_card' ? (
                          <CreditCard className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Landmark className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {account.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {account.institution_name ||
                            account.account_type_display ||
                            account.type}
                        </p>
                      </div>
                      <span
                        className={cn(
                          'text-sm font-semibold tabular-nums',
                          (account.balance ?? 0) >= 0
                            ? 'text-green-500'
                            : 'text-red-500'
                        )}
                      >
                        {formatCurrency(
                          account.balance ?? 0,
                          preferences.currency,
                          0
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Transactions */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Users className="h-5 w-5" />
                  Recent Shared Transactions
                </CardTitle>
                <Link
                  to="/data"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  View all
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {transactions.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">
                  No shared transactions yet.
                </p>
              ) : (
                <div className="divide-y divide-border/50">
                  {transactions.map(txn => (
                    <div
                      key={txn.id}
                      className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {txn.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {txn.account_name} ·{' '}
                          {txn.category_name || 'Uncategorized'} · {txn.date}
                        </p>
                      </div>
                      <span
                        className={cn(
                          'text-sm font-semibold tabular-nums whitespace-nowrap',
                          txn.transaction_type === 'credit'
                            ? 'text-green-500'
                            : 'text-foreground'
                        )}
                      >
                        {txn.transaction_type === 'credit' ? '+' : '-'}
                        {formatCurrency(txn.amount, preferences.currency)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
