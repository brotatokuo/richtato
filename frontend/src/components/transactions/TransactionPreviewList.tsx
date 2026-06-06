import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Transaction } from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import { AlertTriangle } from 'lucide-react';

interface TransactionPreviewListProps {
  transactions: Transaction[];
  loading?: boolean;
  error?: string | null;
  emptyMessage?: string;
  showAccount?: boolean;
  showCategory?: boolean;
  variant?: 'plain' | 'card';
}

export function TransactionPreviewList({
  transactions,
  loading = false,
  error = null,
  emptyMessage = 'No transactions found.',
  showAccount = true,
  showCategory = true,
  variant = 'plain',
}: TransactionPreviewListProps) {
  const { preferences } = usePreferences();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <AlertTriangle className="h-8 w-8 text-red-500 mb-2" />
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div
      className={variant === 'card' ? 'space-y-2' : 'divide-y divide-border/50'}
    >
      {transactions.map(transaction => (
        <TransactionPreviewRow
          key={transaction.id}
          transaction={transaction}
          showAccount={showAccount}
          showCategory={showCategory}
          variant={variant}
          currency={preferences.currency ?? 'USD'}
          dateFormat={preferences.date_format ?? 'MM/DD/YYYY'}
        />
      ))}
    </div>
  );
}

interface TransactionPreviewRowProps {
  transaction: Transaction;
  showAccount: boolean;
  showCategory: boolean;
  variant: 'plain' | 'card';
  currency: string;
  dateFormat: string;
}

function TransactionPreviewRow({
  transaction,
  showAccount,
  showCategory,
  variant,
  currency,
  dateFormat,
}: TransactionPreviewRowProps) {
  const isCredit = transaction.transaction_type === 'credit';
  const amount = Math.abs(Number(transaction.amount));
  const metadata = [
    formatDate(transaction.date, dateFormat),
    showAccount ? transaction.account_name : null,
    showCategory ? transaction.category_name || 'Uncategorized' : null,
  ].filter(Boolean);

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3',
        variant === 'card'
          ? 'rounded-lg border border-border/50 bg-muted/30 p-3 transition-colors hover:bg-muted/50'
          : 'py-2.5 first:pt-0 last:pb-0'
      )}
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {transaction.description || '-'}
        </p>
        <p className="text-xs text-muted-foreground truncate">
          {metadata.join(' / ')}
        </p>
      </div>
      <span
        className={cn(
          'text-sm font-semibold tabular-nums whitespace-nowrap',
          isCredit ? 'text-green-600' : 'text-red-600'
        )}
      >
        {isCredit ? '+' : '-'}
        {formatCurrency(amount, currency)}
      </span>
    </div>
  );
}
