import { AccountsSection } from '@/components/asset_dashboard/AccountsSection';
import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { SavingsChart } from '@/components/asset_dashboard/SavingsChart';
import { Modal } from '@/components/ui/Modal';
import { dashboardApiService } from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle, PiggyBank, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AssetDashboardData {
  networth: string;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  total_income: string;
  total_expenses: string;
}

export function AssetDashboard() {
  const [dashboardData, setDashboardData] = useState<AssetDashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const stableSavingsChart = useMemo(() => <SavingsChart />, []);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<any | null>(null);
  const [history, setHistory] = useState<
    Array<{ id: number; date: string; amount: string }>
  >([]);
  const [balanceInput, setBalanceInput] = useState('');
  const [dateInput, setDateInput] = useState('');
  const [accountsReloadKey, setAccountsReloadKey] = useState(0);
  const [txPage, setTxPage] = useState(1);
  const [txPageSize, setTxPageSize] = useState(10);
  const [txTotal, setTxTotal] = useState(0);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from multiple APIs
      const [
        dashboardMetrics,
        accounts,
        incomeTransactions,
        expenseTransactions,
      ] = await Promise.all([
        dashboardApiService.getDashboardMetrics(),
        transactionsApiService.getAccounts(),
        transactionsApiService.getIncomeTransactions(),
        transactionsApiService.getExpenseTransactions(),
      ]);

      // Helper to coerce currency strings or numbers to a number
      const parseAmountToNumber = (value: unknown): number => {
        if (typeof value === 'number') return value;
        if (typeof value === 'string') {
          const normalized = value.replace(/[^0-9.-]+/g, '');
          const parsed = parseFloat(normalized);
          return isNaN(parsed) ? 0 : parsed;
        }
        if (typeof value === 'bigint') return Number(value);
        return 0;
      };

      // Calculate total assets from accounts
      const totalAssets = accounts.reduce((sum, account) => {
        const balanceNumber = parseAmountToNumber((account as any).balance);
        return sum + balanceNumber;
      }, 0);

      // Calculate total income and expenses
      const totalIncome = incomeTransactions.reduce(
        (sum, transaction) =>
          sum + parseAmountToNumber((transaction as any).amount),
        0
      );
      const totalExpenses = expenseTransactions.reduce(
        (sum, transaction) =>
          sum + parseAmountToNumber((transaction as any).amount),
        0
      );

      // Calculate net worth (simplified as total assets for now)
      const netWorth = totalAssets;

      setDashboardData({
        networth: `$${netWorth.toLocaleString()}`,
        networth_growth: dashboardMetrics.networth_growth,
        networth_growth_class: dashboardMetrics.networth_growth_class,
        savings_rate: dashboardMetrics.savings_rate,
        savings_rate_class: dashboardMetrics.savings_rate_class,
        savings_rate_context: dashboardMetrics.savings_rate_context,
        total_income: `$${totalIncome.toLocaleString()}`,
        total_expenses: `$${totalExpenses.toLocaleString()}`,
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

  const openAccountModal = async (account: any) => {
    try {
      setSelectedAccount(account);
      setBalanceInput(String(account.balance ?? ''));
      const today = new Date();
      const toIso = (d: Date) =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      setDateInput(account.lastUpdated || toIso(today));
      setTxPage(1);
      const tx = await transactionsApiService.getAccountTransactions(
        account.id,
        { page: 1, pageSize: txPageSize }
      );
      setHistory(tx.rows || []);
      setTxTotal(tx.total || 0);
      setAccountModalOpen(true);
    } catch (e) {
      setHistory([]);
      setTxTotal(0);
      setAccountModalOpen(true);
    }
  };

  const reloadHistoryPage = async (page: number, pageSize: number) => {
    if (!selectedAccount) return;
    const tx = await transactionsApiService.getAccountTransactions(
      selectedAccount.id,
      { page, pageSize }
    );
    setHistory(tx.rows || []);
    setTxTotal(tx.total || 0);
  };

  const saveAccountUpdate = async () => {
    if (!selectedAccount) return;
    const amount = Number(String(balanceInput).replace(/[^0-9.-]+/g, ''));
    if (!dateInput || isNaN(amount)) return;
    await transactionsApiService.createAccountTransaction({
      account: selectedAccount.id,
      amount,
      date: dateInput,
    });
    await reloadHistoryPage(1, txPageSize);
    setTxPage(1);
    setAccountsReloadKey(v => v + 1);
  };

  const editHistoryRow = async (row: {
    id: number;
    date: string;
    amount: string;
  }) => {
    if (!selectedAccount) return;
    const amountNumber = Number(String(row.amount).replace(/[^0-9.-]+/g, ''));
    await transactionsApiService.updateAccountTransaction(selectedAccount.id, {
      id: row.id,
      amount: amountNumber,
      date: row.date,
    });
    await reloadHistoryPage(txPage, txPageSize);
    setAccountsReloadKey(v => v + 1);
  };

  const deleteHistoryRow = async (rowId: number) => {
    if (!selectedAccount) return;
    await transactionsApiService.deleteAccountTransaction(
      selectedAccount.id,
      rowId
    );
    // If deleting last row on last page, move back a page
    const newTotal = Math.max(0, txTotal - 1);
    const maxPage = Math.max(1, Math.ceil(newTotal / txPageSize));
    const nextPage = Math.min(txPage, maxPage);
    setTxPage(nextPage);
    setTxTotal(newTotal);
    await reloadHistoryPage(nextPage, txPageSize);
    setAccountsReloadKey(v => v + 1);
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">
          Loading asset dashboard data...
        </div>
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
      {/* Asset KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 w-full min-w-0">
        <MetricCard
          title="Net Worth"
          value={dashboardData.networth}
          subtitle={dashboardData.networth_growth}
          icon={<TrendingUp className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Net Worth = Sum of all account balances.
              </p>
              <p>
                Currently simplified to total assets across linked accounts.
              </p>
            </div>
          }
        />

        <MetricCard
          title="Savings Rate"
          value={dashboardData.savings_rate}
          subtitle={dashboardData.savings_rate_context}
          icon={<PiggyBank className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Savings Rate = (Income - Expenses) / Income.
              </p>
              <p>Income and expenses are summed over the selected period.</p>
            </div>
          }
        />

        {/* Removed Investment Performance card until backed by real data */}
      </div>

      {/* Main Asset Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-1 w-full min-w-0">
        {/* Savings Trend */}
        <div className="w-full overflow-x-auto">{stableSavingsChart}</div>

        {/* Accounts */}
        <div className="lg:col-span-2 w-full overflow-x-auto">
          <AccountsSection
            onAccountClick={openAccountModal}
            reloadKey={accountsReloadKey}
          />
        </div>
      </div>

      {/* Account Update Modal */}
      <Modal
        isOpen={accountModalOpen}
        onClose={() => setAccountModalOpen(false)}
        title={
          selectedAccount ? `Update ${selectedAccount.name}` : 'Update Account'
        }
      >
        {selectedAccount && (
          <div className="space-y-4">
            {/* Trend chart at top */}
            <div className="pt-2">
              <TrendFromHistory rows={history} />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-sm text-muted-foreground mb-1">
                  Balance
                </label>
                <input
                  className="w-full border rounded-md px-3 py-2 bg-background"
                  value={balanceInput}
                  onChange={e => setBalanceInput(e.target.value)}
                  inputMode="decimal"
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">
                  Date
                </label>
                <input
                  className="w-full border rounded-md px-3 py-2 bg-background"
                  type="date"
                  value={dateInput}
                  onChange={e => setDateInput(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 rounded-md border"
                onClick={() => setAccountModalOpen(false)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-md bg-primary text-primary-foreground"
                onClick={saveAccountUpdate}
              >
                Save
              </button>
            </div>

            <div className="pt-4">
              <h4 className="font-medium mb-2">Past Updates</h4>
              <div className="overflow-x-auto border rounded-md">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-muted/40 text-left">
                      <th className="px-3 py-2">Date</th>
                      <th className="px-3 py-2">Amount</th>
                      <th className="px-3 py-2 w-24">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map(row => (
                      <EditableHistoryRow
                        key={row.id}
                        row={row}
                        onSave={editHistoryRow}
                        onDelete={() => deleteHistoryRow(row.id)}
                      />
                    ))}
                    {history.length === 0 && (
                      <tr>
                        <td
                          className="px-3 py-4 text-muted-foreground"
                          colSpan={3}
                        >
                          No past updates
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {/* Pagination controls */}
              <div className="flex items-center justify-between mt-3">
                <div className="text-sm text-muted-foreground">
                  Page {txPage} of{' '}
                  {Math.max(1, Math.ceil(txTotal / txPageSize))}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="px-3 py-1 border rounded disabled:opacity-50"
                    disabled={txPage <= 1}
                    onClick={async () => {
                      const next = Math.max(1, txPage - 1);
                      setTxPage(next);
                      await reloadHistoryPage(next, txPageSize);
                    }}
                  >
                    Prev
                  </button>
                  <button
                    className="px-3 py-1 border rounded disabled:opacity-50"
                    disabled={
                      txPage >= Math.max(1, Math.ceil(txTotal / txPageSize))
                    }
                    onClick={async () => {
                      const maxPage = Math.max(
                        1,
                        Math.ceil(txTotal / txPageSize)
                      );
                      const next = Math.min(maxPage, txPage + 1);
                      setTxPage(next);
                      await reloadHistoryPage(next, txPageSize);
                    }}
                  >
                    Next
                  </button>
                  <select
                    className="border rounded px-2 py-1"
                    value={txPageSize}
                    onChange={async e => {
                      const ps = Number(e.target.value) || 10;
                      setTxPageSize(ps);
                      setTxPage(1);
                      await reloadHistoryPage(1, ps);
                    }}
                  >
                    {[5, 10, 20, 50].map(s => (
                      <option key={s} value={s}>
                        {s} / page
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function EditableHistoryRow({
  row,
  onSave,
  onDelete,
}: {
  row: { id: number; date: string; amount: string };
  onSave: (row: {
    id: number;
    date: string;
    amount: string;
  }) => void | Promise<void>;
  onDelete: () => void | Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [localDate, setLocalDate] = useState(row.date);
  const [localAmount, setLocalAmount] = useState(row.amount);

  return (
    <tr className="border-t">
      <td className="px-3 py-2">
        {editing ? (
          <input
            type="date"
            className="border rounded px-2 py-1 bg-background"
            value={localDate}
            onChange={e => setLocalDate(e.target.value)}
          />
        ) : (
          row.date
        )}
      </td>
      <td className="px-3 py-2">
        {editing ? (
          <input
            className="border rounded px-2 py-1 bg-background"
            value={localAmount}
            onChange={e => setLocalAmount(e.target.value)}
          />
        ) : (
          row.amount
        )}
      </td>
      <td className="px-3 py-2">
        {editing ? (
          <div className="flex gap-2">
            <button
              className="px-2 py-1 border rounded"
              onClick={async () => {
                await onSave({
                  id: row.id,
                  date: localDate,
                  amount: localAmount,
                });
                setEditing(false);
              }}
            >
              Save
            </button>
            <button
              className="px-2 py-1 border rounded"
              onClick={() => {
                setLocalDate(row.date);
                setLocalAmount(row.amount);
                setEditing(false);
              }}
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              className="px-2 py-1 border rounded"
              onClick={() => setEditing(true)}
            >
              Edit
            </button>
            <button className="px-2 py-1 border rounded" onClick={onDelete}>
              Delete
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}

function TrendFromHistory({
  rows,
}: {
  rows: Array<{ date: string; amount: string }>;
}) {
  const labels = rows.map(r => r.date);
  const values = rows.map(r =>
    Number(String(r.amount).replace(/[^0-9.-]+/g, ''))
  );
  const options = {
    tooltip: {
      trigger: 'axis',
    },
    xAxis: { type: 'category', data: labels },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (v: number) => '$' + Number(v ?? 0).toLocaleString(),
      },
    },
  };
  return (
    <div className="border rounded-md p-2">
      <SavingsLine
        data={{
          series: [
            {
              type: 'line',
              name: 'Balance',
              data: values,
              smooth: true,
              lineStyle: { color: '#16a34a', width: 2 },
              itemStyle: { color: '#16a34a' },
            },
          ],
        }}
        options={options}
      />
    </div>
  );
}

import { BaseChart } from '@/components/asset_dashboard/BaseChart';
function SavingsLine({ data, options }: { data: any; options: any }) {
  return <BaseChart type="line" data={data} options={options} height={200} />;
}
