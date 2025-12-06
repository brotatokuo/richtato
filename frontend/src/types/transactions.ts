import { Transaction } from '@/lib/api/transactions';

export interface TransactionFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
  category?: string;
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
  typeFilter: TransactionTypeFilter;
}

// Display transaction interface (different from API)
export interface DisplayTransaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  account: string;
  transactionType: 'debit' | 'credit';
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
    amount: Number(apiTransaction.signed_amount),
    account: apiTransaction.account_name || 'Unknown',
    transactionType: apiTransaction.transaction_type,
  };
};
