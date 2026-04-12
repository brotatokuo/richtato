import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ColumnDef, DataTable } from '@/components/ui/DataTable';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import {
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

interface TransactionItem {
  id: number;
  date: string;
  description: string;
  amount: string;
  transaction_type: 'credit' | 'debit';
}

interface AccountHistoryPanelProps {
  account: AccountWithBalance;
  onClose: () => void;
  onDataChange?: () => void;
}

interface BalancePoint {
  date: string;
  balance: number;
}

export function AccountHistoryPanel({
  account,
  onClose,
  onDataChange,
}: AccountHistoryPanelProps) {
  const { preferences } = usePreferences();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [balanceHistory, setBalanceHistory] = useState<BalancePoint[]>([]);
  const [balanceError, setBalanceError] = useState<string | null>(null);
  const [balanceLoading, setBalanceLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<TransactionItem | null>(
    null
  );
  const [showTable, setShowTable] = useState(false);

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await transactionsApiService.getAccountTransactions(
        account.id,
        {
          page: 1,
          pageSize: 50,
        }
      );
      setTransactions(data.rows || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load transactions'
      );
    } finally {
      setLoading(false);
    }
  }, [account.id]);

  const fetchBalanceHistory = useCallback(async () => {
    setBalanceLoading(true);
    setBalanceError(null);
    try {
      const data = await transactionsApiService.getAccountBalanceHistory(
        account.id
      );
      setBalanceHistory(data?.data_points || []);
    } catch (err) {
      setBalanceError(
        err instanceof Error ? err.message : 'Failed to load balance history'
      );
      setBalanceHistory([]);
    } finally {
      setBalanceLoading(false);
    }
  }, [account.id]);

  useEffect(() => {
    fetchTransactions();
    fetchBalanceHistory();
  }, [fetchTransactions, fetchBalanceHistory]);

  // Chart data - show balance over time (carry forward last known balance)
  const chartData = useMemo(() => {
    if (balanceHistory.length === 0) return { series: [], dates: [] };

    // Sort ascending by date
    const sortedByDate = [...balanceHistory].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const dateLabels = sortedByDate.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    });

    const balanceSeries = sortedByDate.map(d => d.balance);

    return {
      dates: dateLabels,
      series: [
        {
          name: 'Balance',
          type: 'line',
          data: balanceSeries,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
            color: '#22c55e',
          },
          itemStyle: {
            color: '#22c55e',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(34, 197, 94, 0.18)' },
                { offset: 1, color: 'rgba(34, 197, 94, 0.02)' },
              ],
            },
          },
        },
      ],
    };
  }, [balanceHistory]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: {
          color: '#f3f4f6',
        },
        formatter: function (params: Array<{ name?: string; value?: number }>) {
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
    [chartData, preferences.currency]
  );

  // Calculate total credits and debits
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

  const handleRowClick = (item: TransactionItem) => {
    setSelectedItem(item);
    setShowEditModal(true);
  };

  const handleAddSubmit = async (data: { balance: number; date: string }) => {
    try {
      const result = await transactionsApiService.createAccountTransaction({
        account: account.id,
        amount: data.balance,
        date: data.date,
      });

      const txType = data.balance >= 0 ? 'credit' : 'debit';
      const newItem: TransactionItem = {
        id: result.id,
        date: data.date,
        description: 'Balance update',
        amount: result.amount,
        transaction_type: txType as 'credit' | 'debit',
      };
      setTransactions(prev =>
        [newItem, ...prev].sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        )
      );

      setShowAddModal(false);
      onDataChange?.();
      fetchBalanceHistory();
    } catch (error) {
      console.error('Error adding transaction:', error);
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
      const result = await transactionsApiService.updateAccountTransaction(
        account.id,
        {
          id: data.id,
          amount: data.balance,
          date: data.date,
        }
      );

      setTransactions(prev =>
        prev
          .map(t =>
            t.id === data.id
              ? { ...t, amount: result.amount, date: result.date }
              : t
          )
          .sort(
            (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
          )
      );

      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
      fetchBalanceHistory();
    } catch (error) {
      console.error('Error updating transaction:', error);
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!selectedItem) return;
    const confirmDelete = window.confirm('Delete this transaction?');
    if (!confirmDelete) return;

    try {
      await transactionsApiService.deleteAccountTransaction(
        account.id,
        selectedItem.id
      );

      setTransactions(prev => prev.filter(t => t.id !== selectedItem.id));

      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
      fetchBalanceHistory();
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

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

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 border-t-2 border-t-primary">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <History className="h-5 w-5 text-primary" />
            <div>
              <span className="text-lg">{account.name}</span>
              <span className="text-sm font-normal text-muted-foreground ml-2">
                Transactions
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
              Add Transaction
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
        {/* Transaction summary */}
        {transactionSummary && (
          <div className="flex items-center justify-between gap-4 p-3 rounded-lg bg-muted/30 text-sm">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-muted-foreground">Credits:</span>
              <span className="font-medium text-green-500">
                {formatCurrency(
                  transactionSummary.totalCredits,
                  preferences.currency
                )}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <span className="text-muted-foreground">Debits:</span>
              <span className="font-medium text-red-500">
                {formatCurrency(
                  transactionSummary.totalDebits,
                  preferences.currency
                )}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Net:</span>
              <span
                className={`font-semibold ${transactionSummary.net >= 0 ? 'text-green-500' : 'text-red-500'}`}
              >
                {transactionSummary.net >= 0 ? '+' : ''}
                {formatCurrency(transactionSummary.net, preferences.currency)}
              </span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="h-48 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-600 mb-2">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchTransactions}>
                Retry
              </Button>
            </div>
          </div>
        ) : transactions.length === 0 && balanceHistory.length === 0 ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No transactions yet.</p>
              <p className="text-sm mt-1">
                Sync your account or add transactions manually.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chart */}
            {chartData.series.length > 0 ? (
              <BaseChart
                type="line"
                data={{ series: chartData.series }}
                options={chartOptions}
                height={180}
              />
            ) : balanceLoading ? (
              <div className="h-48 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : balanceError ? (
              <div className="h-48 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-red-600 mb-2">{balanceError}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchBalanceHistory}
                  >
                    Retry
                  </Button>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No balance history yet.</p>
                  <p className="text-sm mt-1">
                    Add balance updates to track changes over time.
                  </p>
                </div>
              </div>
            )}

            {/* Collapsible DataTable */}
            {transactions.length > 0 && (
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
                      onRowClick={handleRowClick}
                      defaultSortField="date"
                      defaultSortDirection="desc"
                      pageSize={10}
                      emptyMessage="No transactions found."
                      renderMobileCard={renderMobileCard}
                    />
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </CardContent>

      {/* Add Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title={`Add Transaction - ${account.name}`}
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
          title="Edit Transaction"
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
