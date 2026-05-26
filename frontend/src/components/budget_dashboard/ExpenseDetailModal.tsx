import { TransactionPreviewList } from '@/components/transactions/TransactionPreviewList';
import { Modal } from '@/components/ui/Modal';
import { usePreferences } from '@/contexts/PreferencesContext';
import { formatCurrency } from '@/lib/format';
import { Transaction, transactionsApiService } from '@/lib/api/transactions';
import type { MonthlyBudgetData } from '@/lib/api/budget-dashboard';
import { TrendingDown, TrendingUp } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface ExpenseDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  monthData: MonthlyBudgetData | null;
}

export function ExpenseDetailModal({
  isOpen,
  onClose,
  monthData,
}: ExpenseDetailModalProps) {
  const { preferences } = usePreferences();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'transactions'>(
    'summary'
  );

  const fetchTransactions = useCallback(async () => {
    if (!monthData) return;

    try {
      setLoading(true);
      setError(null);

      const transactions: Transaction[] = [];
      let page = 1;
      let hasNext = true;

      while (hasNext) {
        const response = await transactionsApiService.getTransactions({
          startDate: monthData.start_date,
          endDate: monthData.end_date,
          type: 'debit',
          page,
          pageSize: 500,
        });
        transactions.push(...response.transactions);
        hasNext = Boolean(response.has_next);
        page += 1;
      }

      // Sort by date descending
      const txns = [...transactions].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
      );

      setTransactions(txns);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load transactions'
      );
    } finally {
      setLoading(false);
    }
  }, [monthData]);

  useEffect(() => {
    if (isOpen && monthData) {
      fetchTransactions();
    }
  }, [isOpen, monthData, fetchTransactions]);

  if (!monthData) return null;

  const isOverBudget = monthData.percentage > 100;
  const currency = preferences.currency ?? 'USD';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${monthData.label} Budget Details`}
    >
      <div className="space-y-6">
        {/* Summary Header */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">Budget</div>
            <div className="text-lg font-semibold text-foreground">
              {formatCurrency(monthData.total_budget, currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">Spent</div>
            <div
              className={`text-lg font-semibold ${isOverBudget ? 'text-red-500' : 'text-foreground'}`}
            >
              {formatCurrency(monthData.total_spent, currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">
              {isOverBudget ? 'Over' : 'Remaining'}
            </div>
            <div
              className={`text-lg font-semibold ${isOverBudget ? 'text-red-500' : 'text-emerald-500'}`}
            >
              {isOverBudget ? (
                <>
                  <TrendingUp className="inline h-4 w-4 mr-1" />
                  {formatCurrency(
                    Math.abs(monthData.total_remaining),
                    currency
                  )}
                </>
              ) : (
                <>
                  <TrendingDown className="inline h-4 w-4 mr-1" />
                  {formatCurrency(monthData.total_remaining, currency)}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Budget Used</span>
            <span
              className={`font-medium ${isOverBudget ? 'text-red-500' : 'text-foreground'}`}
            >
              {monthData.percentage}%
            </span>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                isOverBudget
                  ? 'bg-red-500'
                  : monthData.percentage > 80
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(monthData.percentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'summary'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setActiveTab('summary')}
          >
            Category Summary
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'transactions'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setActiveTab('transactions')}
          >
            Transactions ({transactions.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="max-h-80 overflow-y-auto">
          {activeTab === 'summary' ? (
            <CategorySummary
              categories={monthData.categories}
              currency={currency}
            />
          ) : (
            <TransactionPreviewList
              transactions={transactions}
              loading={loading}
              error={error}
              emptyMessage="No transactions for this month"
              showAccount
              showCategory
              variant="card"
            />
          )}
        </div>
      </div>
    </Modal>
  );
}

interface CategorySummaryProps {
  categories: MonthlyBudgetData['categories'];
  currency: string;
}

function CategorySummary({ categories, currency }: CategorySummaryProps) {
  if (!categories || categories.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No budget categories for this month
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {categories.map((cat, idx) => {
        const isOver = cat.percentage > 100;
        return (
          <div
            key={idx}
            className="p-3 bg-muted/30 rounded-lg border border-border/50"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-foreground">
                {cat.category}
              </span>
              <span
                className={`text-sm font-semibold ${isOver ? 'text-red-500' : 'text-muted-foreground'}`}
              >
                {cat.percentage}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
              <div
                className={`h-full transition-all ${
                  isOver
                    ? 'bg-red-500'
                    : cat.percentage > 80
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(cat.percentage, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>
                {formatCurrency(cat.spent, currency)} of{' '}
                {formatCurrency(cat.budget, currency)}
              </span>
              <span className={isOver ? 'text-red-500' : 'text-emerald-500'}>
                {isOver ? 'Over by ' : ''}
                {formatCurrency(Math.abs(cat.remaining), currency)}
                {isOver ? '' : ' left'}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
