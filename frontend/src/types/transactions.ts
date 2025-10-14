import { Transaction } from '@/lib/api/transactions';

export interface TransactionFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
  category?: string;
}

export type TransactionType = 'income' | 'expense';

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
  type: TransactionType;
  transactions: DisplayTransaction[];
  onTransactionsChange: (transactions: DisplayTransaction[]) => void;
}

// Display transaction interface (different from API)
export interface DisplayTransaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  account: string;
}

// Helper function to transform API transaction to display format
export const transformTransaction = (
  apiTransaction: Transaction
): DisplayTransaction => {
  return {
    id: apiTransaction.id.toString(),
    date: apiTransaction.date,
    description: apiTransaction.description,
    category: apiTransaction.Category || 'Uncategorized',
    amount: apiTransaction.amount,
    account: apiTransaction.Account || 'Unknown',
  };
};
