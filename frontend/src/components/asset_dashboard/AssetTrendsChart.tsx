import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import {
  AccountGroup,
  AccountWithBalance,
} from '@/components/asset_dashboard/AccountsList';
import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ColumnDef, DataTable } from '@/components/ui/DataTable';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Download,
  RefreshCw,
  Scale,
  TableProperties,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

type RangePreset = '30' | '90' | '180' | '365' | 'custom';

interface BalancePoint {
  date: string;
  balance: number;
}

interface AccountHistory {
  account: AccountWithBalance;
  history: BalancePoint[];
}

interface TransactionItem {
  id: number;
  date: string;
  description: string;
  amount: string;
  transaction_type: 'credit' | 'debit';
}

interface AssetTrendsChartProps {
  selectedAccount: AccountWithBalance | null;
  selectedGroup: AccountGroup | null;
  onResetSelection: () => void;
  onDataChange?: () => void;
  quickBalanceTrigger?: number;
}

const ACCOUNT_COLORS = [
  '#22c55e',
  '#3b82f6',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#f97316',
  '#84cc16',
  '#ef4444',
  '#14b8a6',
];

function getPresetDays(preset: RangePreset): number {
  switch (preset) {
    case '30':
      return 30;
    case '90':
      return 90;
    case '180':
      return 180;
    case '365':
      return 365;
    default:
      return 180;
  }
}

export function AssetTrendsChart({
  selectedAccount,
  selectedGroup,
  onResetSelection,
  onDataChange,
  quickBalanceTrigger,
}: AssetTrendsChartProps) {
  const { preferences } = usePreferences();
  const [histories, setHistories] = useState<AccountHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rangePreset, setRangePreset] = useState<RangePreset>('180');
  const [customStart, setCustomStart] = useState<string>('');
  const [customEnd, setCustomEnd] = useState<string>('');
  const [showDataPanel, setShowDataPanel] = useState(false);

  // Transaction-related state
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [transactionsError, setTransactionsError] = useState<string | null>(
    null
  );
  const [showBalanceModal, setShowBalanceModal] = useState(false);
  const [showTable, setShowTable] = useState(false);

  useEffect(() => {
    if (quickBalanceTrigger && selectedAccount) {
      setShowBalanceModal(true);
    }
  }, [quickBalanceTrigger]); // eslint-disable-line react-hooks/exhaustive-deps

  const effectiveDays = useMemo(() => {
    if (rangePreset !== 'custom') {
      return getPresetDays(rangePreset);
    }
    if (customStart && customEnd) {
      const start = new Date(customStart);
      const end = new Date(customEnd);
      const diff = Math.max(
        1,
        Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      );
      return diff;
    }
    return 180;
  }, [rangePreset, customStart, customEnd]);

  const loadAccountsAndHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const accountList = await transactionsApiService.getAccounts();
      const histories = await fetchHistories(
        accountList as AccountWithBalance[],
        effectiveDays
      );
      setHistories(histories);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load asset trends'
      );
      setHistories([]);
    } finally {
      setLoading(false);
    }
  }, [effectiveDays]);

  useEffect(() => {
    loadAccountsAndHistory();
  }, [loadAccountsAndHistory]);

  const fetchHistories = async (
    accountList: AccountWithBalance[],
    days: number
  ): Promise<AccountHistory[]> => {
    const results = await Promise.all(
      accountList.map(async account => {
        try {
          const data = await transactionsApiService.getAccountBalanceHistory(
            account.id,
            { days }
          );
          return {
            account,
            history: data?.data_points || [],
          };
        } catch (err) {
          console.error('Error fetching history for account', account.id, err);
          return { account, history: [] };
        }
      })
    );
    return results;
  };

  const fetchTransactions = useCallback(async () => {
    if (!selectedAccount) return;

    setTransactionsLoading(true);
    setTransactionsError(null);
    try {
      const data = await transactionsApiService.getAccountTransactions(
        selectedAccount.id,
        {
          page: 1,
          pageSize: 50,
        }
      );
      setTransactions(data.rows || []);
    } catch (err) {
      setTransactionsError(
        err instanceof Error ? err.message : 'Failed to load transactions'
      );
    } finally {
      setTransactionsLoading(false);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (selectedAccount) {
      fetchTransactions();
    } else {
      setTransactions([]);
      setTransactionsError(null);
    }
  }, [selectedAccount, fetchTransactions]);

  const refreshSingleAccountHistory = useCallback(async () => {
    if (!selectedAccount) return;
    try {
      const data = await transactionsApiService.getAccountBalanceHistory(
        selectedAccount.id,
        { days: effectiveDays }
      );
      setHistories(prev =>
        prev.map(h =>
          h.account.id === selectedAccount.id
            ? { ...h, history: data?.data_points || [] }
            : h
        )
      );
    } catch (err) {
      console.error('Error refreshing account history:', err);
    }
  }, [selectedAccount, effectiveDays]);

  const handleSetBalance = async (data: { balance: number; date: string }) => {
    if (!selectedAccount) return;

    try {
      await transactionsApiService.setAccountBalance({
        account: selectedAccount.id,
        balance: data.balance,
        date: data.date,
      });

      setShowBalanceModal(false);
      onDataChange?.();
      refreshSingleAccountHistory();
    } catch (error) {
      console.error('Error setting balance:', error);
      throw error;
    }
  };

  const contextLabel = useMemo(() => {
    if (selectedAccount) return `Account • ${selectedAccount.name}`;
    if (selectedGroup) return `Group • ${selectedGroup.typeDisplay}`;
    return 'All Accounts';
  }, [selectedAccount, selectedGroup]);

  // Transaction summary calculation
  const transactionSummary = useMemo(() => {
    if (transactions.length === 0) return null;
    let totalCredits = 0;
    let totalDebits = 0;
    transactions.forEach(t => {
      const amount = parseFloat(t.amount) || 0;
      if (t.transaction_type === 'credit') {
        totalCredits += amount;
      } else {
        totalDebits += amount;
      }
    });
    return { totalCredits, totalDebits, net: totalCredits - totalDebits };
  }, [transactions]);

  // DataTable column definitions
  const columns: ColumnDef<TransactionItem>[] = useMemo(
    () => [
      {
        field: 'date',
        label: 'Date',
        sortable: true,
        filterable: true,
        width: 'w-28',
        render: (value: string) => (
          <span className="text-muted-foreground">
            {formatDate(value, preferences.date_format)}
          </span>
        ),
      },
      {
        field: 'description',
        label: 'Description',
        sortable: true,
        filterable: true,
        render: (value: string) => (
          <span className="max-w-[200px] truncate block">{value || '—'}</span>
        ),
      },
      {
        field: 'amount',
        label: 'Amount',
        sortable: true,
        align: 'right',
        width: 'w-28',
        render: (value: string, row: TransactionItem) => {
          const amount = parseFloat(value);
          const isDebit = row.transaction_type === 'debit';
          return (
            <span
              className={`font-medium ${isDebit ? 'text-red-500' : 'text-green-600'}`}
            >
              {isDebit ? '-' : '+'}
              {formatCurrency(amount, preferences.currency)}
            </span>
          );
        },
      },
    ],
    [preferences.currency, preferences.date_format]
  );

  // Mobile card renderer for DataTable
  const renderMobileCard = ({
    row,
    onClick,
  }: {
    row: TransactionItem;
    onClick?: () => void;
  }) => {
    const amount = parseFloat(row.amount);
    const isDebit = row.transaction_type === 'debit';
    return (
      <div
        className="p-4 flex justify-between items-start cursor-pointer hover:bg-muted/50"
        onClick={onClick}
      >
        <div className="space-y-1 min-w-0 pr-2">
          <div className="text-sm font-medium truncate">
            {row.description || '—'}
          </div>
          <div className="text-xs text-muted-foreground">
            {formatDate(row.date, preferences.date_format)}
          </div>
        </div>
        <div
          className={`font-medium ${isDebit ? 'text-red-500' : 'text-green-600'}`}
        >
          {isDebit ? '-' : '+'}
          {formatCurrency(amount, preferences.currency)}
        </div>
      </div>
    );
  };

  const chartData = useMemo(() => {
    if (histories.length === 0)
      return {
        series: [],
        dates: [],
        rows: [] as Array<{ date: string; label: string; value: number }>,
      };

    const selectedAccountId = selectedAccount?.id ?? null;
    const selectedGroupType = selectedGroup?.type ?? null;

    // Filter histories relevant to context (but keep others for totals)
    const relevantHistories = histories.filter(h => {
      if (selectedAccountId) return h.account.id === selectedAccountId;
      if (selectedGroupType) return h.account.type === selectedGroupType;
      return true;
    });

    const allHistoriesForTotals = histories;

    // Collect all unique dates from relevant and totals
    const allDates = new Set<string>();
    allHistoriesForTotals.forEach(({ history }) => {
      history.forEach(h => allDates.add(h.date));
    });
    const sortedDates = Array.from(allDates).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );
    const dateLabels = sortedDates.map(d => {
      const date = new Date(d);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    });

    // Helper to build data points with carry-forward (cached per account)
    const seriesCache = new Map<number, number[]>();
    const buildSeriesData = (accountId: number, history: BalancePoint[]) => {
      if (seriesCache.has(accountId)) return seriesCache.get(accountId)!;
      const balanceMap = new Map<string, number>();
      history.forEach(h => balanceMap.set(h.date, h.balance));
      let lastKnown = 0;
      const result = sortedDates.map(date => {
        if (balanceMap.has(date)) lastKnown = balanceMap.get(date)!;
        return lastKnown;
      });
      seriesCache.set(accountId, result);
      return result;
    };

    // Build series list
    const series: Array<{
      name: string;
      type: 'line';
      data: number[];
      smooth: boolean;
      symbol: string;
      symbolSize: number;
      lineStyle: { width: number; color: string };
      itemStyle: { color: string };
      areaStyle?: {
        color?: {
          type: string;
          x: number;
          y: number;
          x2: number;
          y2: number;
          colorStops: Array<{ offset: number; color: string }>;
        };
      };
    }> = [];

    const rows: Array<{ date: string; label: string; value: number }> = [];

    const addSeries = (
      name: string,
      color: string,
      dataPoints: number[],
      withArea = false
    ) => {
      series.push({
        name,
        type: 'line',
        data: dataPoints,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2, color },
        itemStyle: { color },
        ...(withArea
          ? {
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [
                    { offset: 0, color: `${color}30` },
                    { offset: 1, color: `${color}05` },
                  ],
                },
              },
            }
          : {}),
      });
      dataPoints.forEach((v, idx) => {
        rows.push({ date: sortedDates[idx], label: name, value: v });
      });
    };

    if (selectedAccountId && relevantHistories.length > 0) {
      const accHistory = relevantHistories[0];
      const accData = buildSeriesData(
        accHistory.account.id,
        accHistory.history
      );
      addSeries(accHistory.account.name, '#22c55e', accData, true);
    } else if (selectedGroupType) {
      relevantHistories.forEach((h, idx) => {
        const dataPoints = buildSeriesData(h.account.id, h.history);
        const color = ACCOUNT_COLORS[idx % ACCOUNT_COLORS.length];
        addSeries(h.account.name, color, dataPoints, idx === 0);
      });
      const groupData = sortedDates.map((_, i) =>
        relevantHistories.reduce(
          (sum, h) => sum + buildSeriesData(h.account.id, h.history)[i],
          0
        )
      );
      addSeries(
        `${selectedGroup?.typeDisplay || 'Group'} total`,
        '#ffffff',
        groupData
      );
    } else {
      // Default: per-type traces + total
      const historiesByType = new Map<string, AccountHistory[]>();
      histories.forEach(h => {
        const key = h.account.type || 'other';
        if (!historiesByType.has(key)) historiesByType.set(key, []);
        historiesByType.get(key)!.push(h);
      });

      Array.from(historiesByType.entries()).forEach(([type, items], idx) => {
        const dataPoints = sortedDates.map((_, i) =>
          items.reduce(
            (sum, h) => sum + buildSeriesData(h.account.id, h.history)[i],
            0
          )
        );
        const color = ACCOUNT_COLORS[idx % ACCOUNT_COLORS.length];
        addSeries(type, color, dataPoints, idx === 0);
      });

      const totalData = sortedDates.map((_, i) =>
        histories.reduce(
          (sum, h) => sum + buildSeriesData(h.account.id, h.history)[i],
          0
        )
      );
      addSeries('Total', '#ffffff', totalData);
    }

    return { series, dates: dateLabels, rows };
  }, [histories, selectedAccount, selectedGroup]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: { color: '#f3f4f6' },
        formatter: function (
          params: Array<{
            name?: string;
            seriesName?: string;
            value?: number;
            color?: string;
          }>
        ) {
          const date = params?.[0]?.name ?? '';
          const lines = (params || []).map(p => {
            const value = p.value ?? 0;
            const color = p.color;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>${p.seriesName}: ${formatCurrency(value, preferences.currency)}`;
          });
          return [date, ...lines].join('<br/>');
        },
      },
      legend: {
        data: chartData.series.map(s => s.name),
        bottom: 0,
        textStyle: { color: '#9ca3af' },
        icon: 'circle',
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: chartData.dates,
        axisLabel: {
          color: '#9ca3af',
          rotate: chartData.dates.length > 12 ? 45 : 0,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: function (value: number) {
            if (Math.abs(value) >= 1000) {
              return `${(value / 1000).toFixed(0)}K`;
            }
            return formatCurrency(value, preferences.currency, 0);
          },
          color: '#9ca3af',
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '18%',
        top: '12%',
        containLabel: true,
      },
    }),
    [chartData, preferences.currency]
  );

  const exportCsv = () => {
    if (chartData.rows.length === 0) return;
    const header = 'date,label,balance';
    const body = chartData.rows
      .map(r => `${r.date},${r.label.replace(/,/g, '')},${r.value}`)
      .join('\n');
    const csv = `${header}\n${body}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'asset_trends.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const disableCustomRange = rangePreset !== 'custom';

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 w-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex flex-col gap-3">
          {/* Top row: title and context */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-lg">Asset Trends</span>
              <span className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary whitespace-nowrap">
                {contextLabel}
              </span>
              {(selectedAccount || selectedGroup) && (
                <Button
                  size="xs"
                  variant="ghost"
                  onClick={onResetSelection}
                  className="h-7 px-2 gap-1"
                >
                  <RefreshCw className="h-3 w-3" />
                  Reset
                </Button>
              )}
            </div>
            {selectedAccount && (
              <Button
                size="sm"
                onClick={() => setShowBalanceModal(true)}
                className="gap-1"
              >
                <Scale className="h-4 w-4" />
                <span className="hidden sm:inline">Set Balance</span>
              </Button>
            )}
          </div>
          {/* Bottom row: range controls */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-1 sm:gap-2">
              {(['30', '90', '180', '365'] as RangePreset[]).map(preset => (
                <Button
                  key={preset}
                  size="xs"
                  variant={rangePreset === preset ? 'default' : 'ghost'}
                  onClick={() => setRangePreset(preset)}
                  className="transition-all hover:scale-105"
                >
                  {preset}d
                </Button>
              ))}
              <Button
                size="xs"
                variant={rangePreset === 'custom' ? 'default' : 'ghost'}
                onClick={() => setRangePreset('custom')}
                className="gap-1 transition-all hover:scale-105"
              >
                <Calendar className="h-3 w-3" />
                <span className="hidden xs:inline">Custom</span>
              </Button>
            </div>
            <Button
              size="pill"
              variant="outline"
              onClick={() => setShowDataPanel(true)}
              className="gap-1.5 transition-all hover:scale-105"
            >
              <TableProperties className="h-4 w-4" />
              <span className="hidden sm:inline">Data</span>
            </Button>
          </div>
        </CardTitle>
        {rangePreset === 'custom' && (
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <Input
              type="date"
              value={customStart}
              onChange={e => setCustomStart(e.target.value)}
              disabled={rangePreset !== 'custom'}
              className="w-full sm:w-36"
            />
            <span className="text-sm text-muted-foreground hidden sm:inline">
              to
            </span>
            <Input
              type="date"
              value={customEnd}
              onChange={e => setCustomEnd(e.target.value)}
              disabled={disableCustomRange}
              className="w-full sm:w-36"
            />
          </div>
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-72 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="h-72 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-600 mb-2">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={loadAccountsAndHistory}
              >
                Retry
              </Button>
            </div>
          </div>
        ) : chartData.series.length === 0 ? (
          <div className="h-72 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p>No balance history yet.</p>
              <p className="text-sm mt-1">Add balance updates to see trends.</p>
            </div>
          </div>
        ) : (
          <BaseChart
            type="line"
            data={{ series: chartData.series }}
            options={chartOptions}
            height={340}
          />
        )}

        {/* Transaction summary and table - shown when an account is selected */}
        {selectedAccount && (
          <div className="space-y-4 mt-6">
            {/* Transaction summary */}
            {transactionSummary && (
              <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-muted/30 text-sm">
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    <span className="text-muted-foreground text-xs sm:text-sm">
                      Credits
                    </span>
                  </div>
                  <span className="font-medium text-green-500 text-xs sm:text-sm">
                    {formatCurrency(
                      transactionSummary.totalCredits,
                      preferences.currency
                    )}
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                  <div className="flex items-center gap-1">
                    <TrendingDown className="h-4 w-4 text-red-500" />
                    <span className="text-muted-foreground text-xs sm:text-sm">
                      Debits
                    </span>
                  </div>
                  <span className="font-medium text-red-500 text-xs sm:text-sm">
                    {formatCurrency(
                      transactionSummary.totalDebits,
                      preferences.currency
                    )}
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                  <span className="text-muted-foreground text-xs sm:text-sm">
                    Net
                  </span>
                  <span
                    className={`font-semibold text-xs sm:text-sm ${transactionSummary.net >= 0 ? 'text-green-500' : 'text-red-500'}`}
                  >
                    {transactionSummary.net >= 0 ? '+' : ''}
                    {formatCurrency(
                      transactionSummary.net,
                      preferences.currency
                    )}
                  </span>
                </div>
              </div>
            )}

            {/* Collapsible DataTable */}
            {transactionsLoading ? (
              <div className="h-24 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : transactionsError ? (
              <div className="h-24 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-red-600 mb-2">{transactionsError}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchTransactions}
                  >
                    Retry
                  </Button>
                </div>
              </div>
            ) : transactions.length > 0 ? (
              <div>
                <button
                  onClick={() => setShowTable(!showTable)}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full justify-between p-2 rounded hover:bg-muted/30"
                >
                  <span>
                    {transactions.length} transaction
                    {transactions.length !== 1 && 's'}
                  </span>
                  {showTable ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </button>

                {showTable && (
                  <div className="mt-2">
                    <DataTable
                      data={transactions}
                      columns={columns}
                      searchable
                      searchPlaceholder="Search transactions..."
                      searchFields={['description']}
                      defaultSortField="date"
                      defaultSortDirection="desc"
                      pageSize={10}
                      emptyMessage="No transactions found."
                      renderMobileCard={renderMobileCard}
                    />
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </CardContent>

      {/* Data side panel */}
      {showDataPanel && (
        <div className="fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setShowDataPanel(false)}
          />
          <div className="absolute right-0 top-0 h-full w-full sm:max-w-md bg-card border-l border-border/50 shadow-2xl flex flex-col">
            <div className="p-4 flex items-center justify-between border-b border-border/50">
              <div className="space-y-1">
                <div className="font-semibold">Trend Data</div>
                <div className="text-xs text-muted-foreground">
                  {contextLabel} • {chartData.rows.length} points
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={exportCsv}
                  className="gap-1"
                >
                  <Download className="h-4 w-4" />
                  CSV
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setShowDataPanel(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 space-y-2 text-sm">
              {chartData.rows.length === 0 ? (
                <div className="text-muted-foreground">No data to show.</div>
              ) : (
                chartData.rows.map((row, idx) => (
                  <div
                    key={`${row.date}-${row.label}-${idx}`}
                    className="flex items-center justify-between border-b border-border/30 py-1"
                  >
                    <div>
                      <div className="font-medium">{row.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {row.date}
                      </div>
                    </div>
                    <div className="font-semibold">
                      {formatCurrency(row.value, preferences.currency)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Set Balance Modal */}
      {selectedAccount && (
        <Modal
          isOpen={showBalanceModal}
          onClose={() => setShowBalanceModal(false)}
          title={`Set Balance - ${selectedAccount.name}`}
        >
          <AccountBalanceForm
            accountId={selectedAccount.id}
            accountName={selectedAccount.name}
            onSubmit={handleSetBalance}
            onCancel={() => setShowBalanceModal(false)}
          />
        </Modal>
      )}
    </Card>
  );
}
