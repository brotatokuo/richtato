import { Transaction } from '@/lib/api/transactions';

export interface TransactionFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
  category?: string;
  notes?: string;
  transactionType: 'debit' | 'credit';
}

export type TransactionTypeFilter = 'all' | 'credit' | 'debit';

export interface FilterOption {
  label: string;
  value: string;
  count: number;
}

export interface ContextMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  onClose: () => void;
  options: FilterOption[];
  onSelect: (value: string) => void;
  title: string;
}

export interface TransactionTableProps {
  transactions: DisplayTransaction[];
  onTransactionsChange: (transactions: DisplayTransaction[]) => void;
  onRecategorizeClick?: () => void;
}

// Display transaction interface (different from API)
export interface DisplayTransaction {
  id: string;
  date: string;
  description: string;
  category: string;
  categoryType:
    | 'income'
    | 'expense'
    | 'transfer'
    | 'investment'
    | 'other'
    | 'uncategorized';
  amount: number;
  computedRunningBalance?: number | null;
  statementRunningBalance?: number | null;
  runningBalanceDiff?: number | null;
  account: string;
  transactionType: 'debit' | 'credit';
  notes?: string | null;
}

// Helper function to transform API transaction to display format
export const transformTransaction = (
  apiTransaction: Transaction
): DisplayTransaction => {
  return {
    id: apiTransaction.id.toString(),
    date: apiTransaction.date,
    description: apiTransaction.description,
    category: apiTransaction.category_name || 'Uncategorized',
    categoryType: apiTransaction.category_type,
    amount: Number(apiTransaction.signed_amount),
    computedRunningBalance:
      apiTransaction.computed_running_balance != null
        ? Number(apiTransaction.computed_running_balance)
        : null,
    statementRunningBalance:
      apiTransaction.statement_running_balance != null
        ? Number(apiTransaction.statement_running_balance)
        : null,
    runningBalanceDiff:
      apiTransaction.running_balance_diff != null
        ? Number(apiTransaction.running_balance_diff)
        : null,
    account: apiTransaction.account_name || 'Unknown',
    transactionType: apiTransaction.transaction_type,
    notes: apiTransaction.notes ?? '',
  };
};
