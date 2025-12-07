import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ColumnDef, DataTable } from '@/components/ui/DataTable';
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

export function AccountHistoryPanel({
  account,
  onClose,
  onDataChange,
}: AccountHistoryPanelProps) {
  const { preferences } = usePreferences();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
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
          pageSize: 500, // Fetch more so DataTable can handle pagination
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

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // Chart data - show transaction amounts over time
  const chartData = useMemo(() => {
    if (transactions.length === 0) return { series: [], dates: [] };

    const sortedByDate = [...transactions].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const dates = sortedByDate.map(t => {
      const date = new Date(t.date);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    });

    const amounts = sortedByDate.map(t => {
      const amount = parseFloat(t.amount) || 0;
      // Show debits as negative for visual clarity
      return t.transaction_type === 'debit' ? -amount : amount;
    });

    return {
      dates,
      series: [
        {
          name: 'Amount',
          type: 'bar',
          data: amounts,
          itemStyle: {
            color: (params: any) => {
              return params.value >= 0 ? '#22c55e' : '#ef4444';
            },
          },
        },
      ],
    };
  }, [transactions]);

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
          const type = value >= 0 ? 'Credit' : 'Debit';
          return `${date}<br/>${type}: ${formatCurrency(Math.abs(value), preferences.currency)}`;
        },
      },
      xAxis: {
        type: 'category',
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
            return formatCurrency(Math.abs(value), preferences.currency, 0);
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
          <span className="max-w-[200px] truncate block">
            {value || '—'}
          </span>
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
      await transactionsApiService.createAccountTransaction({
        account: account.id,
        amount: data.balance,
        date: data.date,
      });
      await fetchTransactions();
      setShowAddModal(false);
      onDataChange?.();
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
      await transactionsApiService.updateAccountTransaction(account.id, {
        id: data.id,
        amount: data.balance,
        date: data.date,
      });
      await fetchTransactions();
      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
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
      await fetchTransactions();
      setShowEditModal(false);
      setSelectedItem(null);
      onDataChange?.();
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
                {formatCurrency(transactionSummary.totalCredits, preferences.currency)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <span className="text-muted-foreground">Debits:</span>
              <span className="font-medium text-red-500">
                {formatCurrency(transactionSummary.totalDebits, preferences.currency)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Net:</span>
              <span className={`font-semibold ${transactionSummary.net >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {transactionSummary.net >= 0 ? '+' : ''}
                {formatCurrency(transactionSummary.net, preferences.currency)}
              </span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="h-48 flex items-center justify-center">
            <div className="text-muted-foreground">Loading transactions...</div>
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
        ) : transactions.length === 0 ? (
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
            <BaseChart
              type="line"
              data={{ series: chartData.series }}
              options={chartOptions}
              height={180}
            />

            {/* Collapsible DataTable */}
            <div>
              <button
                onClick={() => setShowTable(!showTable)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full justify-between p-2 rounded hover:bg-muted/30"
              >
                <span>
                  {transactions.length} transaction{transactions.length !== 1 && 's'}
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
