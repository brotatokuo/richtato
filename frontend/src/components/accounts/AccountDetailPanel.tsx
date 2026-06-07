import { StorageLocationPanel } from '@/components/accounts/StorageLocationPanel';
import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import { canSetBalanceOnDate } from '@/components/accounts/accountBalanceOnDate';
import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { AccountDetailModal } from '@/components/settings/AccountDetailModal';
import { TransactionsPanel } from '@/components/transactions/TransactionsPanel';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useHousehold } from '@/contexts/HouseholdContext';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService, type SyncMode } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import { getEntityLogo } from '@/lib/imageMapping';
import { cn } from '@/lib/utils';
import {
  ArrowUpDown,
  Edit2,
  FileText,
  Landmark,
  LineChart,
  Plus,
  TrendingDown,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { AccountWithBalance } from './AccountsSidebar';
import type { InstitutionFieldChoice } from './AccountFormFields';

interface BalancePoint {
  date: string;
  balance: number;
}

interface BalanceSnapshotRow extends BalancePoint {
  change: number | null;
}

type AccountDetailTab = 'balance' | 'transactions' | 'statements';

interface AccountDetailPanelProps {
  account: AccountWithBalance | null;
  onAccountUpdated: (updatedAccount?: AccountWithBalance | null) => void;
}

export function AccountDetailPanel({
  account,
  onAccountUpdated,
}: AccountDetailPanelProps) {
  const { preferences } = usePreferences();
  const { isInHousehold } = useHousehold();
  const [balanceHistory, setBalanceHistory] = useState<BalancePoint[]>([]);
  const [chartLoading, setChartLoading] = useState(false);

  const [activeTab, setActiveTab] = useState<AccountDetailTab>('balance');
  const [showEdit, setShowEdit] = useState(false);
  const [showBalanceDialog, setShowBalanceDialog] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [isShared, setIsShared] = useState(
    account?.shared_with_household ?? false
  );

  const [accountTypeOptions, setAccountTypeOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [entityOptions, setEntityOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [institutions, setInstitutions] = useState<InstitutionFieldChoice[]>(
    []
  );
  const canShowTransactions =
    account?.sync_capabilities?.transactions !== false;
  const canShowStatements =
    account?.sync_capabilities?.statement_files !== false;
  const visibleTabCount =
    1 + (canShowTransactions ? 1 : 0) + (canShowStatements ? 1 : 0);
  const canUpdateBalance = account ? canSetBalanceOnDate(account) : false;

  useEffect(() => {
    transactionsApiService
      .getAccountFieldChoices()
      .then(c => {
        setAccountTypeOptions(c.type || []);
        setEntityOptions(c.entity || []);
        setInstitutions(c.institutions || []);
      })
      .catch(() => {});
  }, []);

  const fetchBalanceHistory = useCallback(async (accountId: number) => {
    setChartLoading(true);

    transactionsApiService
      .getAccountBalanceHistory(accountId)
      .then(d => setBalanceHistory(d?.data_points || []))
      .catch(() => setBalanceHistory([]))
      .finally(() => setChartLoading(false));
  }, []);

  useEffect(() => {
    if (!account) return;
    setActiveTab('balance');
    setBalanceHistory([]);
    setIsShared(account.shared_with_household ?? false);
    fetchBalanceHistory(account.id);
  }, [account, fetchBalanceHistory]);

  useEffect(() => {
    if (!account) return;
    if (
      (activeTab === 'transactions' && !canShowTransactions) ||
      (activeTab === 'statements' && !canShowStatements)
    ) {
      setActiveTab('balance');
    }
  }, [account, activeTab, canShowTransactions, canShowStatements]);

  const chartData = useMemo(() => {
    if (!balanceHistory.length) return { series: [], dates: [] };
    const sorted = [...balanceHistory].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    const isLiability =
      (account?.account_type || account?.type) === 'credit_card';
    const lineColor = isLiability ? '#ef4444' : '#22c55e';
    const areaColorStart = isLiability
      ? 'rgba(239,68,68,0.15)'
      : 'rgba(34,197,94,0.15)';
    const areaColorEnd = isLiability
      ? 'rgba(239,68,68,0.02)'
      : 'rgba(34,197,94,0.02)';

    return {
      dates: sorted.map(d =>
        new Date(d.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })
      ),
      series: [
        {
          name: 'Balance',
          type: 'line',
          data: sorted.map(d => d.balance),
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: lineColor },
          itemStyle: { color: lineColor },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: areaColorStart },
                { offset: 1, color: areaColorEnd },
              ],
            },
          },
        },
      ],
    };
  }, [balanceHistory, account?.account_type, account?.type]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17,24,39,0.95)',
        borderColor: '#374151',
        textStyle: { color: '#f3f4f6' },
        formatter: (params: Array<{ name?: string; value?: number }>) => {
          const date = params?.[0]?.name ?? '';
          const value = params?.[0]?.value ?? 0;
          return `${date}<br/>Balance: ${formatCurrency(value, preferences.currency)}`;
        },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: chartData.dates,
        axisLabel: { color: '#9ca3af', fontSize: 11 },
        axisLine: { lineStyle: { color: '#374151' } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (v: number) => {
            const abs = Math.abs(v);
            if (abs >= 1000) return `${(v / 1000).toFixed(0)}K`;
            return formatCurrency(v, preferences.currency, 0);
          },
          color: '#9ca3af',
          fontSize: 11,
        },
        splitLine: { lineStyle: { color: '#1f2937' } },
      },
      grid: {
        left: '2%',
        right: '2%',
        bottom: '8%',
        top: '8%',
        containLabel: true,
      },
    }),
    [chartData, preferences.currency]
  );

  const balanceRows = useMemo<BalanceSnapshotRow[]>(() => {
    const sorted = [...balanceHistory].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );

    return sorted.map((point, index) => {
      const previousPoint = sorted[index + 1];
      return {
        ...point,
        change: previousPoint ? point.balance - previousPoint.balance : null,
      };
    });
  }, [balanceHistory]);

  const balanceChange = useMemo(() => {
    if (balanceHistory.length < 2) return null;
    const sorted = [...balanceHistory].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
    const latest = sorted[0]?.balance ?? 0;
    const oldest = sorted[sorted.length - 1]?.balance ?? 0;
    return latest - oldest;
  }, [balanceHistory]);

  const handleEdit = async (form: {
    name: string;
    type: string;
    entity: string;
    shared_with_household?: boolean;
    opening_balance?: number | null;
    opening_balance_date?: string | null;
    sync_mode?: SyncMode;
  }) => {
    if (!account) return;
    setEditLoading(true);
    try {
      const updated = await transactionsApiService.updateAccount(account.id, {
        name: form.name,
        type: form.type,
        entity: form.entity,
        shared_with_household: form.shared_with_household,
        sync_mode: form.sync_mode,
        ...(form.opening_balance !== undefined
          ? {
              opening_balance: form.opening_balance,
              opening_balance_date: form.opening_balance_date,
            }
          : {}),
      });

      if (
        form.opening_balance !== undefined &&
        form.opening_balance !== null &&
        (updated.opening_balance === undefined ||
          updated.opening_balance === null)
      ) {
        toast.error('Opening balance did not save', {
          description:
            'The server accepted the update but did not persist opening balance. Restart the backend container and try again.',
        });
        return;
      }

      const updatedWithBalance: AccountWithBalance = {
        ...updated,
        balance:
          typeof updated.balance === 'number'
            ? updated.balance
            : Number(String(updated.balance || '0').replace(/[^0-9.-]+/g, '')),
        lastUpdated: String(updated.date || account.lastUpdated || ''),
      };
      toast.success('Account updated', {
        description:
          form.opening_balance !== undefined
            ? `Opening balance: ${updated.opening_balance ?? 'removed'}`
            : undefined,
      });
      onAccountUpdated(updatedWithBalance);
      setShowEdit(false);
    } catch (e) {
      toast.error('Failed to update', {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!account) return;
    setEditLoading(true);
    try {
      await transactionsApiService.deleteAccount(account.id);
      onAccountUpdated();
      setShowEdit(false);
    } catch (e) {
      toast.error('Failed to delete', {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setEditLoading(false);
    }
  };

  const handleSetBalance = async (data: { balance: number; date: string }) => {
    if (!account) return;

    try {
      const result = await transactionsApiService.setAccountBalance({
        account: account.id,
        balance: data.balance,
        date: data.date,
      });

      const adjustment = Number.parseFloat(result.adjustment);
      if (Number.isNaN(adjustment) || adjustment === 0) {
        toast.success('Balance already matches transactions');
      } else {
        toast.success('Balance reconciled', {
          description: `${formatCurrency(
            Math.abs(adjustment),
            preferences.currency
          )} adjustment added`,
        });
      }

      const updatedBalance = Number.parseFloat(result.balance);
      onAccountUpdated({
        ...account,
        balance: Number.isNaN(updatedBalance)
          ? account.balance
          : updatedBalance,
        lastUpdated: data.date,
      });
      await fetchBalanceHistory(account.id);
      setShowBalanceDialog(false);
    } catch (e) {
      toast.error('Failed to update balance', {
        description: e instanceof Error ? e.message : undefined,
      });
      throw e;
    }
  };

  if (!account) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <Landmark className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-base font-medium text-muted-foreground">
          Select an account
        </p>
        <p className="text-sm text-muted-foreground/60 mt-1">
          Choose an account from the list to view balance history, transactions,
          and statements.
        </p>
      </div>
    );
  }

  const entityLogo = getEntityLogo(account.entity || '');
  const isLiability = (account.account_type || account.type) === 'credit_card';

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Account header */}
      <div className="flex-shrink-0 px-6 py-3 border-b border-border/60">
        <div className="flex items-start gap-2.5">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
            {entityLogo ? (
              <img
                src={entityLogo}
                alt={account.institution_name || ''}
                className="w-5 h-5 object-contain"
              />
            ) : (
              <Landmark className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-base font-semibold text-foreground leading-tight flex items-center gap-1.5 min-w-0">
                <span className="truncate">{account.name}</span>
                {isShared && (
                  <span className="inline-flex items-center gap-0.5 rounded-full bg-primary/10 px-1.5 py-px text-[10px] font-medium text-primary flex-shrink-0">
                    <Users className="h-2.5 w-2.5" />
                    Shared
                  </span>
                )}
              </h2>
              <div className="flex items-center gap-0.5 flex-shrink-0">
                {isInHousehold && (
                  <Button
                    size="sm"
                    variant={isShared ? 'secondary' : 'ghost'}
                    onClick={async () => {
                      const newValue = !isShared;
                      setIsShared(newValue);
                      try {
                        await transactionsApiService.updateAccount(account.id, {
                          shared_with_household: newValue,
                        });
                        onAccountUpdated();
                        toast.success(
                          newValue
                            ? 'Account shared with household'
                            : 'Account is now personal'
                        );
                      } catch (e) {
                        setIsShared(!newValue);
                        toast.error('Failed to update sharing', {
                          description:
                            e instanceof Error ? e.message : undefined,
                        });
                      }
                    }}
                    className="h-7 px-2 text-xs"
                  >
                    <Users className="h-3 w-3 mr-1" />
                    {isShared ? 'Shared' : 'Share'}
                  </Button>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setShowEdit(true)}
                  className="h-7 w-7"
                  title="Edit account"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-muted-foreground flex-wrap">
              <span className="truncate">
                {account.institution_name || account.entity_display || 'Manual'}
              </span>
              {account.account_number_last4 && (
                <span className="text-muted-foreground/60 font-mono flex-shrink-0">
                  ····{account.account_number_last4}
                </span>
              )}
              <Badge
                variant="secondary"
                className="text-[10px] h-4 px-1.5 flex-shrink-0"
              >
                {account.account_type_display ||
                  account.type_display ||
                  'Account'}
              </Badge>
            </div>
            <div className="mt-2.5 pt-2.5 border-t border-border/40">
              <p className="text-xs text-muted-foreground mb-0.5">
                Current Balance
              </p>
              <div className="flex items-end gap-2.5">
                <p
                  className={cn(
                    'text-3xl font-bold tabular-nums leading-none',
                    isLiability ? 'text-red-500' : 'text-foreground'
                  )}
                >
                  {isLiability && account.balance < 0 ? '-' : ''}
                  {formatCurrency(
                    Math.abs(account.balance),
                    preferences.currency
                  )}
                </p>
                {balanceChange !== null && (
                  <div
                    className={cn(
                      'flex items-center gap-1 text-sm font-medium pb-0.5',
                      balanceChange >= 0 ? 'text-green-600' : 'text-red-500'
                    )}
                  >
                    {balanceChange >= 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    {balanceChange >= 0 ? '+' : '-'}
                    {formatCurrency(
                      Math.abs(balanceChange),
                      preferences.currency,
                      0
                    )}
                  </div>
                )}
              </div>
              {account.lastUpdated && (
                <p className="text-xs text-muted-foreground/60 mt-1">
                  Last updated{' '}
                  {new Date(
                    account.lastUpdated + 'T00:00:00'
                  ).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
      <Tabs
        value={activeTab}
        onValueChange={value => setActiveTab(value as AccountDetailTab)}
        className="flex flex-col flex-1 min-h-0"
      >
        <div className="flex-shrink-0 border-b border-border/40 px-6 pt-3 pb-0">
          <TabsList
            className={cn(
              'grid w-full sm:w-auto sm:inline-grid',
              visibleTabCount === 3
                ? 'grid-cols-3'
                : visibleTabCount === 2
                  ? 'grid-cols-2'
                  : 'grid-cols-1'
            )}
          >
            <TabsTrigger
              value="balance"
              className="flex items-center gap-2 text-xs sm:text-sm"
            >
              <LineChart className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span>Balance History</span>
            </TabsTrigger>
            {canShowTransactions && (
              <TabsTrigger
                value="transactions"
                className="flex items-center gap-2 text-xs sm:text-sm"
              >
                <ArrowUpDown className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                <span>Transactions</span>
              </TabsTrigger>
            )}
            {canShowStatements && (
              <TabsTrigger
                value="statements"
                className="flex items-center gap-2 text-xs sm:text-sm"
              >
                <FileText className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                <span>Statements</span>
              </TabsTrigger>
            )}
          </TabsList>
        </div>

        <TabsContent
          value="balance"
          className="mt-0 flex-1 overflow-y-auto px-6 py-4 focus-visible:outline-none"
        >
          {chartLoading ? (
            <div className="h-48 flex items-center justify-center">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-4">
              {canUpdateBalance && (
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowBalanceDialog(true)}
                  >
                    <Plus className="h-4 w-4 mr-1.5" />
                    Update balance
                  </Button>
                </div>
              )}

              {balanceHistory.length < 2 ? (
                <div className="h-48 flex flex-col items-center justify-center text-center">
                  <LineChart className="h-8 w-8 text-muted-foreground/30 mb-2" />
                  <p className="text-sm text-muted-foreground/60">
                    {balanceHistory.length === 0
                      ? 'No balance history yet'
                      : 'Not enough data to show balance history'}
                  </p>
                  {canUpdateBalance && (
                    <p className="text-xs text-muted-foreground/50 mt-1">
                      Enter a balance on a date to start tracking history.
                    </p>
                  )}
                </div>
              ) : (
                <BaseChart
                  type="line"
                  data={chartData}
                  options={chartOptions}
                  height="280px"
                />
              )}

              {balanceRows.length > 0 && (
                <div className="rounded-lg border border-border/60 bg-card/50">
                  <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                    <div>
                      <h3 className="text-sm font-medium text-foreground">
                        Balance History
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        Dated balances from transactions and adjustments
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {balanceRows.length} record
                      {balanceRows.length === 1 ? '' : 's'}
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/30 text-xs uppercase text-muted-foreground">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium">
                            Date
                          </th>
                          <th className="px-4 py-2 text-right font-medium">
                            Balance
                          </th>
                          <th className="px-4 py-2 text-right font-medium">
                            Change
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {balanceRows.map(row => (
                          <tr key={row.date} className="hover:bg-muted/20">
                            <td className="px-4 py-2 text-muted-foreground">
                              {formatDate(row.date, preferences.date_format)}
                            </td>
                            <td className="px-4 py-2 text-right font-medium tabular-nums text-foreground">
                              {formatCurrency(
                                row.balance,
                                preferences.currency
                              )}
                            </td>
                            <td
                              className={cn(
                                'px-4 py-2 text-right font-medium tabular-nums',
                                row.change === null
                                  ? 'text-muted-foreground'
                                  : row.change >= 0
                                    ? 'text-green-600'
                                    : 'text-red-500'
                              )}
                            >
                              {row.change === null
                                ? '—'
                                : `${row.change >= 0 ? '+' : '-'}${formatCurrency(
                                    Math.abs(row.change),
                                    preferences.currency
                                  )}`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </TabsContent>

        {canShowTransactions && (
          <TabsContent
            value="transactions"
            className="mt-0 flex-1 overflow-y-auto px-6 py-4 focus-visible:outline-none"
          >
            <TransactionsPanel
              accountId={account.id}
              defaultAccountId={account.id}
              hiddenColumns={['account']}
              className="min-w-0"
            />
          </TabsContent>
        )}

        {canShowStatements && (
          <TabsContent
            value="statements"
            className="mt-0 flex-1 overflow-y-auto px-6 py-4 focus-visible:outline-none"
          >
            <StorageLocationPanel
              accountId={account.id}
              accountName={account.name}
              storageUri={account.storage_uri}
              resolvedStorageUri={account.resolved_storage_uri}
              onUploadComplete={onAccountUpdated}
            />
          </TabsContent>
        )}
      </Tabs>

      {/* Edit modal */}
      <AccountDetailModal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        account={account}
        onSubmit={handleEdit}
        onDelete={handleDelete}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        institutions={institutions}
        loading={editLoading}
      />

      <Dialog open={showBalanceDialog} onOpenChange={setShowBalanceDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Update balance</DialogTitle>
            <DialogDescription>
              Enter the account balance on a specific date. Richtato will
              reconcile it against your transactions and add an adjustment if
              needed.
            </DialogDescription>
          </DialogHeader>
          <AccountBalanceForm
            accountId={account.id}
            accountName={account.name}
            onSubmit={handleSetBalance}
            onCancel={() => setShowBalanceDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
