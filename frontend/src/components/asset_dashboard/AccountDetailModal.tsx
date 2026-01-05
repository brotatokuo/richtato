import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import { MoreVertical, Pencil, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AccountWithBalance {
  id: number;
  name: string;
  type: string;
  entity?: string;
  balance: number;
  lastUpdated: string;
}

interface HistoryRow {
  id: number;
  date: string;
  amount: string;
}

interface AccountDetailModalProps {
  account: AccountWithBalance | null;
  isOpen: boolean;
  onClose: () => void;
  onAccountUpdated: () => void;
}

export function AccountDetailModal({
  account,
  isOpen,
  onClose,
  onAccountUpdated,
}: AccountDetailModalProps) {
  const { preferences } = usePreferences();
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [balanceInput, setBalanceInput] = useState('');
  const [dateInput, setDateInput] = useState('');
  const [txPage, setTxPage] = useState(1);
  const [txPageSize, setTxPageSize] = useState(10);
  const [txTotal, setTxTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  useEffect(() => {
    if (account && isOpen) {
      loadAccountData();
    }
  }, [account, isOpen]);

  const loadAccountData = async () => {
    if (!account) return;

    setBalanceInput(String(account.balance ?? ''));
    const today = new Date();
    const toIso = (d: Date) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    setDateInput(account.lastUpdated || toIso(today));
    setTxPage(1);

    await reloadHistoryPage(1, txPageSize);
  };

  const reloadHistoryPage = async (page: number, pageSize: number) => {
    if (!account) return;

    try {
      setLoading(true);
      const tx = await transactionsApiService.getAccountTransactions(
        account.id,
        { page, pageSize }
      );
      setHistory(tx.rows || []);
      setTxTotal(tx.total || 0);
    } catch {
      setHistory([]);
      setTxTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const saveAccountUpdate = async () => {
    if (!account) return;
    const amount = Number(String(balanceInput).replace(/[^0-9.-]+/g, ''));
    if (!dateInput || isNaN(amount)) return;

    await transactionsApiService.createAccountTransaction({
      account: account.id,
      amount,
      date: dateInput,
    });

    await reloadHistoryPage(1, txPageSize);
    setTxPage(1);
    onAccountUpdated();
  };

  const editHistoryRow = async (row: HistoryRow) => {
    if (!account) return;
    const amountNumber = Number(String(row.amount).replace(/[^0-9.-]+/g, ''));

    await transactionsApiService.updateAccountTransaction(account.id, {
      id: row.id,
      amount: amountNumber,
      date: row.date,
    });

    await reloadHistoryPage(txPage, txPageSize);
    onAccountUpdated();
  };

  const deleteHistoryRow = async (rowId: number) => {
    if (!account) return;

    await transactionsApiService.deleteAccountTransaction(account.id, rowId);

    // If deleting last row on last page, move back a page
    const newTotal = Math.max(0, txTotal - 1);
    const maxPage = Math.max(1, Math.ceil(newTotal / txPageSize));
    const nextPage = Math.min(txPage, maxPage);
    setTxPage(nextPage);
    setTxTotal(newTotal);

    await reloadHistoryPage(nextPage, txPageSize);
    setDeleteConfirmId(null);
    onAccountUpdated();
  };

  const handlePageSizeChange = async (val: string) => {
    const ps = Number(val) || 10;
    setTxPageSize(ps);
    setTxPage(1);
    await reloadHistoryPage(1, ps);
  };

  const handlePrevPage = async () => {
    const next = Math.max(1, txPage - 1);
    setTxPage(next);
    await reloadHistoryPage(next, txPageSize);
  };

  const handleNextPage = async () => {
    const maxPage = Math.max(1, Math.ceil(txTotal / txPageSize));
    const next = Math.min(maxPage, txPage + 1);
    setTxPage(next);
    await reloadHistoryPage(next, txPageSize);
  };

  if (!account) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`${account.name}`}>
      <div className="space-y-4">
        {/* Trend chart at top */}
        <div className="pt-2">
          <TrendFromHistory rows={history} currency={preferences.currency || 'USD'} />
        </div>

        {/* Balance and Date inputs */}
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

        {/* Action buttons */}
        <div className="flex justify-end gap-2">
          <button className="px-4 py-2 rounded-md border" onClick={onClose}>
            Cancel
          </button>
          <button
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground"
            onClick={saveAccountUpdate}
          >
            Save
          </button>
        </div>

        {/* History section */}
        <div className="pt-4">
          <h4 className="font-medium mb-2">History</h4>

          {loading ? (
            <div className="flex items-center justify-center h-32 border rounded-md">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="overflow-x-auto border rounded-md">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/40 text-left">
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Amount</th>
                    <th className="px-3 py-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(row => (
                    <HistoryRow
                      key={row.id}
                      row={row}
                      currency={preferences.currency || 'USD'}
                      dateFormat={preferences.date_format || 'MM/DD/YYYY'}
                      onSave={editHistoryRow}
                      onDelete={() => setDeleteConfirmId(row.id)}
                      isConfirmingDelete={deleteConfirmId === row.id}
                      onConfirmDelete={() => deleteHistoryRow(row.id)}
                      onCancelDelete={() => setDeleteConfirmId(null)}
                    />
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td
                        className="px-3 py-4 text-center text-muted-foreground"
                        colSpan={3}
                      >
                        No history records found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination controls */}
          <div className="flex items-center justify-between mt-3">
            <div className="text-sm text-muted-foreground">
              Page {txPage} of {Math.max(1, Math.ceil(txTotal / txPageSize))}
            </div>
            <div className="flex items-center gap-2">
              <button
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-secondary hover:text-secondary-foreground transition-colors"
                disabled={txPage <= 1}
                onClick={handlePrevPage}
              >
                Prev
              </button>
              <button
                className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-secondary hover:text-secondary-foreground transition-colors"
                disabled={
                  txPage >= Math.max(1, Math.ceil(txTotal / txPageSize))
                }
                onClick={handleNextPage}
              >
                Next
              </button>
              <div className="min-w-[120px]">
                <Select
                  value={String(txPageSize)}
                  onValueChange={handlePageSizeChange}
                >
                  <SelectTrigger className="h-8">
                    <SelectValue placeholder="Items / page" />
                  </SelectTrigger>
                  <SelectContent position="popper">
                    {[5, 10, 20, 50].map(s => (
                      <SelectItem key={s} value={String(s)}>
                        {s} / page
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}

interface HistoryRowProps {
  row: HistoryRow;
  currency: string;
  dateFormat: string;
  onSave: (row: HistoryRow) => void | Promise<void>;
  onDelete: () => void;
  isConfirmingDelete: boolean;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}

function HistoryRow({
  row,
  currency,
  dateFormat,
  onSave,
  onDelete,
  isConfirmingDelete,
  onConfirmDelete,
  onCancelDelete,
}: HistoryRowProps) {
  const [editing, setEditing] = useState(false);
  const [localDate, setLocalDate] = useState(row.date);
  const [localAmount, setLocalAmount] = useState(row.amount);

  const handleSave = async () => {
    await onSave({
      id: row.id,
      date: localDate,
      amount: localAmount,
    });
    setEditing(false);
  };

  const handleCancel = () => {
    setLocalDate(row.date);
    setLocalAmount(row.amount);
    setEditing(false);
  };

  // Format amount with user preferences
  const formattedAmount = formatCurrency(
    Number(String(row.amount).replace(/[^0-9.-]+/g, '')),
    currency,
    2
  );

  const formattedDate = formatDate(row.date, dateFormat);

  if (isConfirmingDelete) {
    return (
      <tr className="border-t bg-red-50 dark:bg-red-950/20">
        <td colSpan={3} className="px-3 py-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-red-600 dark:text-red-400">
              Delete this record?
            </span>
            <div className="flex gap-2">
              <button
                className="px-3 py-1 text-sm border rounded bg-red-600 text-white hover:bg-red-700 transition-colors"
                onClick={onConfirmDelete}
              >
                Confirm
              </button>
              <button
                className="px-3 py-1 text-sm border rounded hover:bg-muted transition-colors"
                onClick={onCancelDelete}
              >
                Cancel
              </button>
            </div>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-t hover:bg-muted/30 transition-colors">
      <td className="px-3 py-2">
        {editing ? (
          <input
            type="date"
            className="border rounded px-2 py-1 bg-background text-sm"
            value={localDate}
            onChange={e => setLocalDate(e.target.value)}
          />
        ) : (
          formattedDate
        )}
      </td>
      <td className="px-3 py-2">
        {editing ? (
          <input
            className="border rounded px-2 py-1 bg-background text-sm w-full"
            value={localAmount}
            onChange={e => setLocalAmount(e.target.value)}
            inputMode="decimal"
          />
        ) : (
          formattedAmount
        )}
      </td>
      <td className="px-3 py-2">
        {editing ? (
          <div className="flex gap-2">
            <button
              className="px-2 py-1 text-sm border rounded hover:bg-secondary hover:text-secondary-foreground transition-colors"
              onClick={handleSave}
            >
              Save
            </button>
            <button
              className="px-2 py-1 text-sm border rounded hover:bg-muted transition-colors"
              onClick={handleCancel}
            >
              Cancel
            </button>
          </div>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="p-1 hover:bg-muted rounded transition-colors">
                <MoreVertical className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setEditing(true)}>
                <Pencil className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onDelete} className="text-red-600">
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </td>
    </tr>
  );
}

function TrendFromHistory({
  rows,
  currency,
}: {
  rows: Array<{ date: string; amount: string }>;
  currency: string;
}) {
  const labels = rows.map(r => r.date);
  const values = rows.map(r =>
    Number(String(r.amount).replace(/[^0-9.-]+/g, ''))
  );

  const options = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const dataPoint = params[0];
        return `${dataPoint.name}<br/>${formatCurrency(dataPoint.value, currency, 2)}`;
      },
    },
    xAxis: { type: 'category', data: labels },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (v: number) => formatCurrency(v, currency, 0),
      },
    },
  };

  return (
    <div className="border rounded-md p-2">
      <BaseChart
        type="line"
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
        height={200}
      />
    </div>
  );
}
