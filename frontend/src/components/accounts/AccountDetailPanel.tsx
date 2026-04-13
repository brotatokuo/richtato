import { AccountDetailModal } from '@/components/settings/AccountDetailModal';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import { usePreferences } from '@/contexts/PreferencesContext';
import { bankConnectionsApiService } from '@/lib/api/bankConnections';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import { getEntityLogo } from '@/lib/imageMapping';
import { cn } from '@/lib/utils';
import {
  ArrowRight,
  ArrowUpDown,
  Edit2,
  Landmark,
  Loader2,
  RefreshCw,
  Scale,
  TrendingDown,
  TrendingUp,
  Unlink,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { AccountWithBalance } from './AccountsSidebar';
import { AccountBalanceForm } from './AccountBalanceForm';
import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { DisconnectConfirmModal } from '@/components/settings/DisconnectConfirmModal';

interface TransactionRow {
  id: number;
  date: string;
  description: string;
  amount: string;
  transaction_type: 'credit' | 'debit';
}

interface BalancePoint {
  date: string;
  balance: number;
}

interface AccountDetailPanelProps {
  account: AccountWithBalance | null;
  onAccountUpdated: () => void;
}

function timeAgo(isoString: string | null | undefined): string {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function AccountDetailPanel({ account, onAccountUpdated }: AccountDetailPanelProps) {
  const { preferences } = usePreferences();
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<TransactionRow[]>([]);
  const [balanceHistory, setBalanceHistory] = useState<BalancePoint[]>([]);
  const [txLoading, setTxLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const [showEdit, setShowEdit] = useState(false);
  const [showSetBalance, setShowSetBalance] = useState(false);
  const [showDisconnect, setShowDisconnect] = useState(false);
  const [editLoading, setEditLoading] = useState(false);

  const [accountTypeOptions, setAccountTypeOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [entityOptions, setEntityOptions] = useState<Array<{ value: string; label: string }>>([]);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    transactionsApiService.getAccountFieldChoices().then(c => {
      setAccountTypeOptions(c.type || []);
      setEntityOptions(c.entity || []);
    }).catch(() => {});
  }, []);

  const fetchData = useCallback(async (accountId: number) => {
    setTxLoading(true);
    setChartLoading(true);

    transactionsApiService
      .getAccountTransactions(accountId, { page: 1, pageSize: 10 })
      .then(d => setTransactions(d.rows || []))
      .catch(() => setTransactions([]))
      .finally(() => setTxLoading(false));

    transactionsApiService
      .getAccountBalanceHistory(accountId)
      .then(d => setBalanceHistory(d?.data_points || []))
      .catch(() => setBalanceHistory([]))
      .finally(() => setChartLoading(false));
  }, []);

  useEffect(() => {
    if (!account) return;
    setTransactions([]);
    setBalanceHistory([]);
    fetchData(account.id);
  }, [account, fetchData]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const chartData = useMemo(() => {
    if (!balanceHistory.length) return { series: [], dates: [] };
    const sorted = [...balanceHistory].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    const isLiability = (account?.account_type || account?.type) === 'credit_card';
    const lineColor = isLiability ? '#ef4444' : '#22c55e';
    const areaColorStart = isLiability ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)';
    const areaColorEnd = isLiability ? 'rgba(239,68,68,0.02)' : 'rgba(34,197,94,0.02)';

    return {
      dates: sorted.map(d =>
        new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
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
              x: 0, y: 0, x2: 0, y2: 1,
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
      grid: { left: '2%', right: '2%', bottom: '8%', top: '8%', containLabel: true },
    }),
    [chartData, preferences.currency]
  );

  // Balance change from history
  const balanceChange = useMemo(() => {
    if (balanceHistory.length < 2) return null;
    const sorted = [...balanceHistory].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
    const latest = sorted[0]?.balance ?? 0;
    const oldest = sorted[sorted.length - 1]?.balance ?? 0;
    return latest - oldest;
  }, [balanceHistory]);

  const handleSync = async () => {
    if (!account?.connection_id) return;
    setSyncing(true);
    try {
      await bankConnectionsApiService.syncConnection(account.connection_id);
      toast.info('Sync started', { description: 'Syncing transactions...' });
      pollRef.current = setInterval(async () => {
        const progress = await bankConnectionsApiService.getSyncJobProgress(account.connection_id!).catch(() => null);
        if (progress && progress.status !== 'running') {
          if (pollRef.current) clearInterval(pollRef.current);
          setSyncing(false);
          if (progress.status === 'completed') {
            toast.success('Sync completed', { description: `${progress.transactions_synced} transactions synced` });
            fetchData(account.id);
            onAccountUpdated();
          } else {
            toast.error('Sync failed', { description: progress.errors?.[0] });
          }
        }
      }, 1500);
    } catch (e) {
      toast.error('Sync failed', { description: e instanceof Error ? e.message : undefined });
      setSyncing(false);
    }
  };

  const handleEdit = async (form: { name: string; type: string; entity: string; image_key?: string | null }) => {
    if (!account) return;
    setEditLoading(true);
    try {
      await transactionsApiService.updateAccount(account.id, { name: form.name, image_key: form.image_key });
      onAccountUpdated();
      setShowEdit(false);
    } catch (e) {
      toast.error('Failed to update', { description: e instanceof Error ? e.message : undefined });
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
      toast.error('Failed to delete', { description: e instanceof Error ? e.message : undefined });
    } finally {
      setEditLoading(false);
    }
  };

  const handleSetBalance = async (data: { balance: number; date: string }) => {
    if (!account) return;
    await transactionsApiService.setAccountBalance({ account: account.id, balance: data.balance, date: data.date });
    fetchData(account.id);
    onAccountUpdated();
    setShowSetBalance(false);
  };

  const handleDisconnect = async (deleteData: boolean) => {
    if (!account?.connection_id) return;
    setEditLoading(true);
    try {
      await bankConnectionsApiService.deleteConnection(account.connection_id, deleteData);
      onAccountUpdated();
      setShowDisconnect(false);
    } catch (e) {
      toast.error('Failed to disconnect', { description: e instanceof Error ? e.message : undefined });
    } finally {
      setEditLoading(false);
    }
  };

  if (!account) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <Landmark className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-base font-medium text-muted-foreground">Select an account</p>
        <p className="text-sm text-muted-foreground/60 mt-1">
          Choose an account from the list to view details, balance history, and recent transactions.
        </p>
      </div>
    );
  }

  const entityLogo = getEntityLogo(account.entity || '');
  const isLiability = (account.account_type || account.type) === 'credit_card';
  const hasError = account.connection_status === 'error';

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Account header */}
      <div className="px-6 pt-5 pb-4 border-b border-border/60">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
              {entityLogo ? (
                <img src={entityLogo} alt={account.institution_name || ''} className="w-6 h-6 object-contain" />
              ) : (
                <Landmark className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground leading-tight">{account.name}</h2>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                <span className="text-sm text-muted-foreground">
                  {account.institution_name || account.entity_display || 'Manual'}
                </span>
                {account.account_number_last4 && (
                  <span className="text-sm text-muted-foreground/60 font-mono">
                    ····{account.account_number_last4}
                  </span>
                )}
                <Badge variant="secondary" className="text-xs h-5">
                  {account.account_type_display || account.type_display || 'Account'}
                </Badge>
              </div>
            </div>
          </div>

          {/* Sync status chip */}
          {account.has_connection && (
            <div
              className={cn(
                'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium flex-shrink-0',
                hasError
                  ? 'bg-red-500/10 text-red-500'
                  : 'bg-green-500/10 text-green-600'
              )}
            >
              {hasError ? <WifiOff className="h-3 w-3" /> : <Wifi className="h-3 w-3" />}
              {hasError ? 'Sync error' : account.last_sync ? `Synced ${timeAgo(account.last_sync)}` : 'Connected'}
            </div>
          )}
        </div>

        {/* Hero balance */}
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-1">Current Balance</p>
          <div className="flex items-end gap-3">
            <p
              className={cn(
                'text-3xl font-bold tabular-nums',
                isLiability ? 'text-red-500' : 'text-foreground'
              )}
            >
              {isLiability && account.balance < 0 ? '-' : ''}
              {formatCurrency(Math.abs(account.balance), preferences.currency)}
            </p>
            {balanceChange !== null && (
              <div
                className={cn(
                  'flex items-center gap-1 text-sm font-medium pb-1',
                  balanceChange >= 0 ? 'text-green-600' : 'text-red-500'
                )}
              >
                {balanceChange >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                {balanceChange >= 0 ? '+' : '-'}
                {formatCurrency(Math.abs(balanceChange), preferences.currency, 0)}
              </div>
            )}
          </div>
          {account.lastUpdated && (
            <p className="text-xs text-muted-foreground/60 mt-1">
              Last updated {new Date(account.lastUpdated + 'T00:00:00').toLocaleDateString(undefined, {
                month: 'short', day: 'numeric', year: 'numeric',
              })}
            </p>
          )}
        </div>
      </div>

      {/* Balance chart */}
      <div className="px-6 py-4 border-b border-border/40">
        <p className="text-sm font-medium text-muted-foreground mb-3">Balance History</p>
        {chartLoading ? (
          <div className="h-32 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : balanceHistory.length < 2 ? (
          <div className="h-32 flex items-center justify-center">
            <p className="text-sm text-muted-foreground/60">Not enough data to show chart</p>
          </div>
        ) : (
          <BaseChart type="line" data={chartData} options={chartOptions} height="140px" />
        )}
      </div>

      {/* Recent Transactions */}
      <div className="px-6 py-4 flex-1">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-muted-foreground">Recent Transactions</p>
          <button
            onClick={() => navigate(`/data?account=${account.id}`)}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            View all
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        {txLoading ? (
          <div className="flex items-center justify-center h-24">
            <LoadingSpinner />
          </div>
        ) : transactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center">
            <ArrowUpDown className="h-6 w-6 text-muted-foreground/30 mb-2" />
            <p className="text-sm text-muted-foreground/60">No transactions found</p>
          </div>
        ) : (
          <div className="space-y-0">
            {transactions.map((tx, i) => {
              const amount = parseFloat(tx.amount);
              const isDebit = tx.transaction_type === 'debit';
              return (
                <div
                  key={tx.id}
                  className={cn(
                    'flex items-center justify-between py-2.5',
                    i < transactions.length - 1 && 'border-b border-border/30'
                  )}
                >
                  <div className="flex-1 min-w-0 mr-4">
                    <p className="text-sm font-medium text-foreground truncate">
                      {tx.description || '—'}
                    </p>
                    <p className="text-xs text-muted-foreground/70">
                      {formatDate(tx.date, preferences.date_format)}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'text-sm font-semibold tabular-nums flex-shrink-0',
                      isDebit ? 'text-red-500' : 'text-green-600'
                    )}
                  >
                    {isDebit ? '-' : '+'}
                    {formatCurrency(amount, preferences.currency)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="px-6 py-4 border-t border-border/40 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowEdit(true)}
          className="h-8 text-xs"
        >
          <Edit2 className="h-3.5 w-3.5 mr-1.5" />
          Edit
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowSetBalance(true)}
          className="h-8 text-xs"
        >
          <Scale className="h-3.5 w-3.5 mr-1.5" />
          Set Balance
        </Button>
        {account.has_connection && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={handleSync}
              disabled={syncing}
              className="h-8 text-xs"
            >
              {syncing ? (
                <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              )}
              Sync
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowDisconnect(true)}
              className="h-8 text-xs text-muted-foreground hover:text-red-500 hover:border-red-500/40"
            >
              <Unlink className="h-3.5 w-3.5 mr-1.5" />
              Disconnect
            </Button>
          </>
        )}
      </div>

      {/* Edit modal */}
      <AccountDetailModal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        account={account}
        onSubmit={handleEdit}
        onDelete={handleDelete}
        onSync={handleSync}
        onDisconnect={() => { setShowEdit(false); setShowDisconnect(true); }}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={editLoading}
      />

      {/* Set balance modal */}
      <Modal
        isOpen={showSetBalance}
        onClose={() => setShowSetBalance(false)}
        title="Set Balance"
      >
        <AccountBalanceForm
          accountId={account.id}
          accountName={account.name}
          onSubmit={handleSetBalance}
          onCancel={() => setShowSetBalance(false)}
        />
      </Modal>

      {/* Disconnect modal */}
      <DisconnectConfirmModal
        isOpen={showDisconnect}
        onClose={() => setShowDisconnect(false)}
        onConfirm={handleDisconnect}
        loading={editLoading}
        accountName={account.name}
      />
    </div>
  );
}
