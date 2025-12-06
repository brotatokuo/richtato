import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Modal } from '@/components/ui/Modal';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import {
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  History,
  Plus,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { AccountWithBalance } from './AccountsList';
import { BaseChart } from './BaseChart';

interface BalanceHistoryItem {
  id: number;
  date: string;
  amount: string;
}

interface AccountHistoryPanelProps {
  account: AccountWithBalance;
  onClose: () => void;
  onDataChange?: () => void;
}

export function AccountHistoryPanel({
  account,
  onClose,
  onDataChange,
}: AccountHistoryPanelProps) {
  const { preferences } = usePreferences();
  const [history, setHistory] = useState<BalanceHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<BalanceHistoryItem | null>(
    null
  );
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [showTable, setShowTable] = useState(false);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await transactionsApiService.getAccountTransactions(
        account.id,
        {
          page: 1,
          pageSize: 100,
        }
      );
      setHistory(data.rows || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load balance history'
      );
    } finally {
      setLoading(false);
    }
  }, [account.id]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const sortedHistory = useMemo(() => {
    return [...history].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
    });
  }, [history, sortDirection]);

  // Chart data
  const chartData = useMemo(() => {
    if (history.length === 0) return { series: [], dates: [] };

    const sortedByDate = [...history].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const dates = sortedByDate.map(h => {
      const date = new Date(h.date);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    });

    const balances = sortedByDate.map(h => parseFloat(h.amount) || 0);

    return {
      dates,
      series: [
        {
          name: 'Balance',
          type: 'line',
          data: balances,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: account.balance >= 0 ? '#22c55e' : '#ef4444',
          },
          itemStyle: {
            color: account.balance >= 0 ? '#22c55e' : '#ef4444',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color:
                    account.balance >= 0
                      ? 'rgba(34, 197, 94, 0.3)'
                      : 'rgba(239, 68, 68, 0.3)',
                },
                {
                  offset: 1,
                  color:
                    account.balance >= 0
                      ? 'rgba(34, 197, 94, 0.05)'
                      : 'rgba(239, 68, 68, 0.05)',
                },
              ],
            },
          },
        },
      ],
    };
  }, [history, account.balance]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: {
          color: '#f3f4f6',
        },
        formatter: function (params: any) {
          const date = params?.[0]?.name ?? '';
          const value = params?.[0]?.value ?? 0;
          return `${date}<br/>Balance: ${formatCurrency(value, preferences.currency)}`;
        },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: chartData.dates,
        axisLabel: {
          color: '#9ca3af',
          rotate: chartData.dates.length > 10 ? 45 : 0,
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
        bottom: '10%',
        top: '10%',
        containLabel: true,
      },
    }),
    [chartData.dates, preferences.currency]
  );

  // Calculate change from first to last entry
  const balanceChange = useMemo(() => {
    if (history.length < 2) return null;
    const sorted = [...history].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    const first = parseFloat(sorted[0].amount) || 0;
    const last = parseFloat(sorted[sorted.length - 1].amount) || 0;
    const change = last - first;
    const percentChange = first !== 0 ? (change / Math.abs(first)) * 100 : 0;
    return { change, percentChange };
  }, [history]);

  const handleAddSubmit = async (data: { balance: number; date: string }) => {
    try {
      await transactionsApiService.createAccountTransaction({
        account: account.id,
        amount: data.balance,
        date: data.date,
      });
      await fetchHistory();
      setShowAddModal(false);
      onDataChange?.();
    } catch (error) {
      console.error('Error adding balance:', error);
      throw error;
    }
  };

  const handleEditSubmit = async (data: {
    balance: number;
    date: string;
    id?: number;
  }) => {
    if (!selectedItem || !data.id) return;

    try {
      await transactionsApiService.updateAccountTransaction(account.id, {
        id: data.id,
        amount: data.balance,
        date: data.date,
      });
      await fetchHistory();
      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
    } catch (error) {
      console.error('Error updating balance:', error);
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!selectedItem) return;
    const confirmDelete = window.confirm('Delete this balance record?');
    if (!confirmDelete) return;

    try {
      await transactionsApiService.deleteAccountTransaction(
        account.id,
        selectedItem.id
      );
      await fetchHistory();
      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
    } catch (error) {
      console.error('Error deleting balance:', error);
    }
  };

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 border-t-2 border-t-primary">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <History className="h-5 w-5 text-primary" />
            <div>
              <span className="text-lg">{account.name}</span>
              <span className="text-sm font-normal text-muted-foreground ml-2">
                Balance History
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => setShowAddModal(true)}
              className="gap-1"
            >
              <Plus className="h-4 w-4" />
              Add Update
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Balance change summary */}
        {balanceChange && (
          <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
            <div className="flex items-center gap-2">
              {balanceChange.change >= 0 ? (
                <TrendingUp className="h-5 w-5 text-green-500" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-500" />
              )}
              <span className="text-sm text-muted-foreground">
                Change over period:
              </span>
            </div>
            <span
              className={`font-semibold ${
                balanceChange.change >= 0 ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {balanceChange.change >= 0 ? '+' : ''}
              {formatCurrency(balanceChange.change, preferences.currency)} (
              {balanceChange.percentChange >= 0 ? '+' : ''}
              {balanceChange.percentChange.toFixed(1)}%)
            </span>
          </div>
        )}

        {loading ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-muted-foreground">Loading history...</div>
          </div>
        ) : error ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-600 mb-2">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchHistory}>
                Retry
              </Button>
            </div>
          </div>
        ) : history.length === 0 ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No balance history yet.</p>
              <p className="text-sm mt-1">
                Add balance updates to track changes over time.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chart */}
            <BaseChart
              type="line"
              data={{ series: chartData.series }}
              options={chartOptions}
              height={180}
            />

            {/* Collapsible table */}
            <div>
              <button
                onClick={() => setShowTable(!showTable)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full justify-between p-2 rounded hover:bg-muted/30"
              >
                <span>
                  {history.length} balance record{history.length !== 1 && 's'}
                </span>
                {showTable ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>

              {showTable && (
                <div className="mt-2 border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() =>
                            setSortDirection(
                              sortDirection === 'asc' ? 'desc' : 'asc'
                            )
                          }
                        >
                          <div className="flex items-center gap-2">
                            Date
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
                        </TableHead>
                        <TableHead className="text-right">Balance</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedHistory.slice(0, 10).map(item => {
                        const amount = parseFloat(item.amount);
                        return (
                          <TableRow
                            key={item.id}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => {
                              setSelectedItem(item);
                              setShowEditModal(true);
                            }}
                          >
                            <TableCell>
                              {formatDate(item.date, preferences.date_format)}
                            </TableCell>
                            <TableCell
                              className={`text-right font-medium ${
                                amount >= 0 ? 'text-green-600' : 'text-red-500'
                              }`}
                            >
                              {formatCurrency(amount, preferences.currency)}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                  {history.length > 10 && (
                    <div className="p-2 text-center text-sm text-muted-foreground border-t">
                      Showing 10 of {history.length} records
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>

      {/* Add Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title={`Add Balance Update - ${account.name}`}
      >
        <AccountBalanceForm
          accountId={account.id}
          accountName={account.name}
          onSubmit={handleAddSubmit}
          onCancel={() => setShowAddModal(false)}
        />
      </Modal>

      {/* Edit Modal */}
      {selectedItem && (
        <Modal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedItem(null);
          }}
          title="Edit Balance Update"
        >
          <AccountBalanceForm
            accountId={account.id}
            accountName={account.name}
            initialData={{
              balance: selectedItem.amount,
              date: selectedItem.date,
              id: selectedItem.id,
            }}
            onSubmit={handleEditSubmit}
            onDelete={handleDelete}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedItem(null);
            }}
          />
        </Modal>
      )}
    </Card>
  );
}
