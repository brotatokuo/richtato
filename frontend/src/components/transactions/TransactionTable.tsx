import { TransactionForm } from '@/components/transactions/TransactionForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  ColumnFilterPopover,
  FilterOption,
} from '@/components/ui/ColumnFilterPopover';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import { SortableHeader } from '@/components/ui/SortableHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import { formatCurrency, formatDate } from '@/lib/format';
import {
  DisplayTransaction,
  TransactionFormData,
  TransactionTableProps,
  transformTransaction,
} from '@/types/transactions';
import {
  ArrowLeftRight,
  Calendar,
  CreditCard,
  Plus,
  RefreshCw,
  Search,
  Tag,
} from 'lucide-react';
import { Fragment, useEffect, useMemo, useRef, useState } from 'react';

const CATEGORY_TYPE_LABELS: Record<string, string> = {
  income: 'Income',
  expense: 'Expense',
  transfer: 'Transfer',
  investment: 'Investment',
  other: 'Other',
  uncategorized: 'Uncategorized',
};

const getLocalDateString = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export function TransactionTable({
  transactions,
  onTransactionsChange,
  accounts,
  categories,
  loading,
  loadingMore,
  hasMore,
  totalCount,
  onLoadMore,
  onRefresh,
  onRecategorizeClick,
}: TransactionTableProps & {
  accounts: Account[];
  categories: Category[];
  loading: boolean;
  loadingMore?: boolean;
  hasMore?: boolean;
  totalCount?: number;
  onLoadMore?: () => void;
  onRefresh: () => void;
}) {
  const { preferences } = usePreferences();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategories, setFilterCategories] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [sortField, setSortField] = useState<keyof DisplayTransaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Infinite scroll sentinel for loading more pages
  const observerTarget = useRef<HTMLDivElement>(null);

  // Filter options from API (replaces client-side computation)
  const [filterOptions, setFilterOptions] = useState<{
    dates: Array<{ label: string; value: string; count: number }>;
    category_types: Array<{ label: string; value: string; count: number }>;
    categories: Array<{ label: string; value: string; count: number }>;
    accounts: Array<{ label: string; value: string; count: number }>;
    amounts: Array<{ label: string; value: string; count: number }>;
    descriptions: Array<{ label: string; value: string; count: number }>;
  } | null>(null);

  useEffect(() => {
    transactionsApiService.getFilterOptions().then(setFilterOptions);
  }, []);

  // Additional filters (now arrays for multi-select)
  const [dateFilters, setDateFilters] = useState<string[]>([]);
  const [descriptionFilters, setDescriptionFilters] = useState<string[]>([]);
  const [categoryTypeFilters, setCategoryTypeFilters] = useState<string[]>([]);
  const [accountFilters, setAccountFilters] = useState<string[]>([]);
  const [amountFilters, setAmountFilters] = useState<string[]>([]);

  // Column search terms (for filtering while typing in popover)
  const [dateSearch, setDateSearch] = useState('');
  const [descriptionSearch, setDescriptionSearch] = useState('');
  const [categoryTypeSearch, setCategoryTypeSearch] = useState('');
  const [categorySearch, setCategorySearch] = useState('');
  const [accountSearch, setAccountSearch] = useState('');
  const [amountSearch, setAmountSearch] = useState('');

  const [formData, setFormData] = useState<TransactionFormData>({
    description: '',
    date: getLocalDateString(),
    amount: '',
    account_name: '',
    category: '',
    notes: '',
    transactionType: 'debit',
  });

  // Edit modal state
  const [selectedTransaction, setSelectedTransaction] =
    useState<DisplayTransaction | null>(null);
  const [editFormData, setEditFormData] = useState<TransactionFormData>({
    description: '',
    date: getLocalDateString(),
    amount: '',
    account_name: '',
    category: '',
    notes: '',
    transactionType: 'debit',
  });

  const evaluateAmountField = (value: string): string => {
    const val = String(value || '').trim();
    if (!val.startsWith('=')) return val;
    const expr = val.slice(1).trim().replace(/\s+/g, '');
    if (!/^[0-9+\-*/().]+$/.test(expr)) return value;
    try {
      const result = Function('"use strict"; return (' + expr + ')')();
      if (typeof result !== 'number' || !isFinite(result)) return value;
      const normalized = Math.round(result * 100) / 100;
      return String(Math.abs(normalized));
    } catch {
      return value;
    }
  };

  const filteredTransactions = transactions
    .filter(transaction => {
      // Global search bar
      const matchesSearch =
        transaction.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        transaction.account.toLowerCase().includes(searchTerm.toLowerCase()) ||
        transaction.category.toLowerCase().includes(searchTerm.toLowerCase());

      // Checkbox selections
      const matchesCategory =
        filterCategories.length === 0 ||
        filterCategories.includes(transaction.category);
      const matchesDate =
        dateFilters.length === 0 || dateFilters.includes(transaction.date);
      const matchesDescription =
        descriptionFilters.length === 0 ||
        descriptionFilters.includes(transaction.description);
      const matchesCategoryType =
        categoryTypeFilters.length === 0 ||
        categoryTypeFilters.includes(transaction.categoryType);
      const matchesAccount =
        accountFilters.length === 0 ||
        accountFilters.includes(transaction.account);
      const matchesAmount =
        amountFilters.length === 0 ||
        amountFilters.includes(String(transaction.amount));

      // Column search terms (typed in filter popover)
      const matchesDateSearch =
        !dateSearch ||
        transaction.date.toLowerCase().includes(dateSearch.toLowerCase()) ||
        formatDate(transaction.date, preferences.date_format)
          .toLowerCase()
          .includes(dateSearch.toLowerCase());
      const matchesDescriptionSearch =
        !descriptionSearch ||
        transaction.description
          .toLowerCase()
          .includes(descriptionSearch.toLowerCase());
      const matchesCategoryTypeSearch =
        !categoryTypeSearch ||
        transaction.categoryType
          .toLowerCase()
          .includes(categoryTypeSearch.toLowerCase());
      const matchesCategorySearch =
        !categorySearch ||
        transaction.category
          .toLowerCase()
          .includes(categorySearch.toLowerCase());
      const matchesAccountSearch =
        !accountSearch ||
        transaction.account.toLowerCase().includes(accountSearch.toLowerCase());
      const matchesAmountSearch =
        !amountSearch ||
        String(transaction.amount).includes(amountSearch) ||
        formatCurrency(Math.abs(transaction.amount), preferences.currency)
          .toLowerCase()
          .includes(amountSearch.toLowerCase());

      return (
        matchesSearch &&
        matchesCategory &&
        matchesCategoryType &&
        matchesDate &&
        matchesDescription &&
        matchesAccount &&
        matchesAmount &&
        matchesDateSearch &&
        matchesDescriptionSearch &&
        matchesCategoryTypeSearch &&
        matchesCategorySearch &&
        matchesAccountSearch &&
        matchesAmountSearch
      );
    })
    .sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });

  // All filtered transactions are visible (client-side filter on loaded pages)
  const visibleTransactions = filteredTransactions;

  // Infinite scroll: load more when sentinel is visible
  useEffect(() => {
    if (!onLoadMore || !hasMore) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [onLoadMore, hasMore]);

  // Filter options from API, formatted for ColumnFilterPopover
  const dateFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.dates) return [];
    return filterOptions.dates.map(d => ({
      label: formatDate(d.value, preferences.date_format),
      value: d.value,
      count: d.count,
    }));
  }, [filterOptions?.dates, preferences.date_format]);

  const descriptionFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.descriptions) return [];
    return filterOptions.descriptions.map(d => ({
      label: d.label || '(empty)',
      value: d.value,
      count: d.count,
    }));
  }, [filterOptions?.descriptions]);

  const categoryTypeFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.category_types) return [];
    const typeOrder = [
      'income',
      'expense',
      'transfer',
      'investment',
      'other',
      'uncategorized',
    ];
    return [...filterOptions.category_types]
      .sort((a, b) => typeOrder.indexOf(a.value) - typeOrder.indexOf(b.value))
      .map(ct => ({
        label: CATEGORY_TYPE_LABELS[ct.value] || ct.label,
        value: ct.value,
        count: ct.count,
      }));
  }, [filterOptions?.category_types]);

  const categoryFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.categories) return [];
    return filterOptions.categories.map(c => ({
      label: c.label,
      value: c.value,
      count: c.count,
    }));
  }, [filterOptions?.categories]);

  const accountFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.accounts) return [];
    return filterOptions.accounts.map(a => ({
      label: a.label,
      value: a.value,
      count: a.count,
    }));
  }, [filterOptions?.accounts]);

  const amountFilterOptions: FilterOption[] = useMemo(() => {
    if (!filterOptions?.amounts) return [];
    return filterOptions.amounts.map(a => ({
      label: formatCurrency(
        Math.abs(parseFloat(a.value)),
        preferences.currency
      ),
      value: a.value,
      count: a.count,
    }));
  }, [filterOptions?.amounts, preferences.currency]);

  const handleSort = (field: keyof DisplayTransaction) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.description || !formData.amount || !formData.account_name) {
      return;
    }

    try {
      // Resolve account by id from dropdown value
      const account = accounts.find(
        acc => String(acc.id) === String(formData.account_name)
      );
      if (!account) {
        throw new Error('Account not found');
      }

      // Find the category ID
      let categoryId: number | undefined;
      if (formData.category) {
        const category = categories.find(
          cat => String(cat.id) === String(formData.category)
        );
        if (category) {
          categoryId = category.id;
        }
      }

      const rawAmount = evaluateAmountField(formData.amount);
      const amountNum = parseFloat(rawAmount);
      const notesValue = (formData.notes ?? '').trim();

      const newTransaction = await transactionsApiService.createTransaction({
        account_id: account.id,
        date: formData.date,
        amount: amountNum,
        description: formData.description,
        transaction_type: formData.transactionType,
        category_id: categoryId,
        notes: notesValue,
      });

      // Transform and add to local state
      const transformedTransaction = transformTransaction(newTransaction);
      onTransactionsChange([transformedTransaction, ...transactions]);

      // Reset form and close modal
      setFormData({
        description: '',
        date: getLocalDateString(),
        amount: '',
        account_name: '',
        category: '',
        notes: '',
        transactionType: 'debit',
      });
      setShowAddModal(false);
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  const openEditModal = (t: DisplayTransaction) => {
    setSelectedTransaction(t);
    // Find account ID from account name
    const account = accounts.find(acc => acc.name === t.account);
    // Find category ID from category name
    const category = t.category
      ? categories.find(cat => cat.name === t.category)
      : null;

    setEditFormData({
      description: t.description,
      date: t.date,
      amount: Math.abs(t.amount).toString(),
      account_name: account ? String(account.id) : '',
      category: category ? String(category.id) : '',
      notes: t.notes ?? '',
      transactionType: t.transactionType,
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransaction) return;
    try {
      // Resolve account by id from dropdown value
      const account = accounts.find(
        acc => String(acc.id) === String(editFormData.account_name)
      );
      if (!account) throw new Error('Account not found');

      // Find the category ID
      let categoryId: number | undefined;
      if (editFormData.category) {
        const category = categories.find(
          cat => String(cat.id) === String(editFormData.category)
        );
        if (category) {
          categoryId = category.id;
        }
      }

      const rawEditAmount = evaluateAmountField(editFormData.amount);
      const amountValue = parseFloat(rawEditAmount);
      const notesValue = (editFormData.notes ?? '').trim();

      const idNum = Number(selectedTransaction.id);
      const updated = await transactionsApiService.updateTransaction(idNum, {
        description: editFormData.description,
        date: editFormData.date,
        amount: amountValue,
        category_id: categoryId ?? null,
        transaction_type: editFormData.transactionType,
        notes: notesValue,
      });

      const transformed = transformTransaction(updated);
      const next = transactions.map(t =>
        t.id === selectedTransaction.id ? transformed : t
      );
      onTransactionsChange(next);

      setShowEditModal(false);
      setSelectedTransaction(null);
    } catch (error) {
      console.error('Error updating transaction:', error);
    }
  };

  const handleDelete = async () => {
    if (!selectedTransaction) return;
    const confirmDelete = window.confirm('Delete this transaction?');
    if (!confirmDelete) return;
    try {
      const idNum = Number(selectedTransaction.id);
      await transactionsApiService.deleteTransaction(idNum);
      const next = transactions.filter(t => t.id !== selectedTransaction.id);
      onTransactionsChange(next);
      setShowEditModal(false);
      setSelectedTransaction(null);
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

  const getTableHeaders = () => {
    return [
      {
        field: 'date' as keyof DisplayTransaction,
        label: 'Date',
        filterable: true,
      },
      {
        field: 'description' as keyof DisplayTransaction,
        label: 'Description',
        filterable: false,
      },
      {
        field: 'categoryType' as keyof DisplayTransaction,
        label: 'Type',
        filterable: true,
      },
      {
        field: 'category' as keyof DisplayTransaction,
        label: 'Category',
        filterable: true,
      },
      {
        field: 'account' as keyof DisplayTransaction,
        label: 'Account',
        filterable: true,
      },
      {
        field: 'amount' as keyof DisplayTransaction,
        label: 'Amount',
        filterable: false,
      },
    ];
  };

  const renderTableCell = (
    transaction: DisplayTransaction,
    field: keyof DisplayTransaction
  ) => {
    switch (field) {
      case 'date':
        return (
          <TableCell key={String(field)} className="font-medium">
            {formatDate(transaction.date, preferences.date_format)}
          </TableCell>
        );
      case 'description':
        return (
          <TableCell
            key={String(field)}
            className="whitespace-normal break-words break-all"
          >
            {transaction.description}
          </TableCell>
        );
      case 'account':
        return <TableCell key={String(field)}>{transaction.account}</TableCell>;
      case 'categoryType': {
        const typeConfig = {
          income: {
            label: 'Income',
            bgColor: 'bg-emerald-100 dark:bg-emerald-900/20',
            textColor: 'text-emerald-800 dark:text-emerald-400',
          },
          expense: {
            label: 'Expense',
            bgColor: 'bg-orange-100 dark:bg-orange-900/20',
            textColor: 'text-orange-800 dark:text-orange-400',
          },
          transfer: {
            label: 'Transfer',
            bgColor: 'bg-blue-100 dark:bg-blue-900/20',
            textColor: 'text-blue-800 dark:text-blue-400',
          },
          investment: {
            label: 'Investment',
            bgColor: 'bg-purple-100 dark:bg-purple-900/20',
            textColor: 'text-purple-800 dark:text-purple-400',
          },
          other: {
            label: 'Other',
            bgColor: 'bg-gray-100 dark:bg-gray-900/20',
            textColor: 'text-gray-800 dark:text-gray-400',
          },
          uncategorized: {
            label: 'Uncategorized',
            bgColor: 'bg-muted',
            textColor: 'text-muted-foreground',
          },
        };
        const config = typeConfig[transaction.categoryType];
        return (
          <TableCell key={String(field)}>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${config.bgColor} ${config.textColor}`}
            >
              {config.label}
            </span>
          </TableCell>
        );
      }
      case 'category': {
        const isCredit = transaction.transactionType === 'credit';
        const bgColor = isCredit
          ? 'bg-green-100 dark:bg-green-900/20'
          : 'bg-red-100 dark:bg-red-900/20';
        const textColor = isCredit
          ? 'text-green-800 dark:text-green-400'
          : 'text-red-800 dark:text-red-400';
        return (
          <TableCell key={String(field)}>
            <span
              className={`px-2 py-1 rounded text-xs ${bgColor} ${textColor}`}
            >
              {transaction.category}
            </span>
          </TableCell>
        );
      }
      case 'amount': {
        const isCredit = transaction.transactionType === 'credit';
        const sign = isCredit ? '+' : '-';
        const color = isCredit ? 'text-green-600' : 'text-red-600';
        return (
          <TableCell
            key={String(field)}
            className={`text-right font-medium ${color}`}
          >
            {sign}
            {formatCurrency(Math.abs(transaction.amount), preferences.currency)}
          </TableCell>
        );
      }
      default:
        return (
          <TableCell key={String(field)}>
            {String(transaction[field])}
          </TableCell>
        );
    }
  };

  return (
    <div className="space-y-3">
      {/* Header with Search and Filters */}
      <div className="flex items-center gap-4 flex-wrap py-2">
        <h2 className="text-xl font-bold text-card-foreground flex items-center gap-2 shrink-0">
          <ArrowLeftRight className="h-5 w-5 text-primary" />
          Transactions
        </h2>
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <Button
          onClick={() => setShowAddModal(true)}
          variant="default"
          size="sm"
        >
          <Plus className="h-3.5 w-3.5 mr-1.5" />
          Add Transaction
        </Button>
        <Button
          onClick={onRefresh}
          disabled={loading}
          variant="outline"
          size="sm"
          title="Refresh transactions"
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh
        </Button>
        {onRecategorizeClick && (
          <Button
            onClick={onRecategorizeClick}
            disabled={loading || transactions.length === 0}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Recategorize All
          </Button>
        )}
      </div>

      {/* Active filters indicator */}
      {(dateFilters.length > 0 ||
        descriptionFilters.length > 0 ||
        categoryTypeFilters.length > 0 ||
        accountFilters.length > 0 ||
        filterCategories.length > 0 ||
        amountFilters.length > 0 ||
        dateSearch ||
        descriptionSearch ||
        categoryTypeSearch ||
        categorySearch ||
        accountSearch ||
        amountSearch) && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {dateFilters.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/15 text-primary text-xs rounded-full">
              <Calendar className="h-3 w-3" />
              {dateFilters.length === 1
                ? formatDate(dateFilters[0], preferences.date_format)
                : `${dateFilters.length} dates`}
            </span>
          )}
          {descriptionFilters.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full dark:bg-blue-900/20 dark:text-blue-400">
              {descriptionFilters.length === 1
                ? descriptionFilters[0].substring(0, 20) +
                  (descriptionFilters[0].length > 20 ? '...' : '')
                : `${descriptionFilters.length} descriptions`}
            </span>
          )}
          {categoryTypeFilters.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-800 text-xs rounded-full dark:bg-purple-900/20 dark:text-purple-400">
              <Tag className="h-3 w-3" />
              {categoryTypeFilters.length === 1
                ? categoryTypeFilters[0].charAt(0).toUpperCase() +
                  categoryTypeFilters[0].slice(1)
                : `${categoryTypeFilters.length} types`}
            </span>
          )}
          {filterCategories.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-secondary text-secondary-foreground text-xs rounded-full">
              <Tag className="h-3 w-3" />
              {filterCategories.length === 1
                ? filterCategories[0]
                : `${filterCategories.length} categories`}
            </span>
          )}
          {accountFilters.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full dark:bg-green-900/20 dark:text-green-400">
              <CreditCard className="h-3 w-3" />
              {accountFilters.length === 1
                ? accountFilters[0]
                : `${accountFilters.length} accounts`}
            </span>
          )}
          {amountFilters.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 text-xs rounded-full dark:bg-amber-900/20 dark:text-amber-400">
              {amountFilters.length === 1
                ? formatCurrency(
                    Math.abs(parseFloat(amountFilters[0])),
                    preferences.currency
                  )
                : `${amountFilters.length} amounts`}
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setDateFilters([]);
              setDescriptionFilters([]);
              setCategoryTypeFilters([]);
              setAccountFilters([]);
              setFilterCategories([]);
              setAmountFilters([]);
              setDateSearch('');
              setDescriptionSearch('');
              setCategoryTypeSearch('');
              setCategorySearch('');
              setAccountSearch('');
              setAmountSearch('');
            }}
            className="text-xs h-6 px-2"
          >
            Clear all
          </Button>
        </div>
      )}

      {/* Add Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add New Transaction"
      >
        <TransactionForm
          formData={formData}
          onFormChange={setFormData}
          onSubmit={handleSubmit}
          accounts={accounts}
          categories={categories}
        />
      </Modal>

      {/* Mobile list (<= md) */}
      <div className="md:hidden">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-0">
            {loading ? (
              <div className="py-8 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="divide-y">
                {visibleTransactions.map((t, index) => {
                  const isCredit = t.transactionType === 'credit';
                  const sign = isCredit ? '+' : '-';
                  const color = isCredit ? 'text-green-600' : 'text-red-600';
                  return (
                    <div
                      key={`${t.id}-${index}`}
                      className="p-4 w-full flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between cursor-pointer hover:bg-muted/50"
                      onClick={() => openEditModal(t)}
                    >
                      <div className="space-y-1 min-w-0 sm:pr-2">
                        <div className="text-sm font-medium whitespace-normal break-words">
                          {t.description}
                        </div>
                        <div className="text-xs text-muted-foreground whitespace-normal break-words">
                          {formatDate(t.date, preferences.date_format)} •{' '}
                          {t.account} • {t.category}
                        </div>
                      </div>
                      <div
                        className={`sm:ml-4 sm:text-right text-sm font-semibold ${color}`}
                      >
                        {sign}
                        {formatCurrency(
                          Math.abs(t.amount),
                          preferences.currency
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Table (md+) */}
      <div className="hidden md:block overflow-x-auto">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 min-w-0">
          <CardContent className="p-0 min-w-0">
            <div className="min-w-full">
              <Table className="min-w-full table-fixed md:table-auto">
                <TableHeader>
                  <TableRow>
                    {getTableHeaders().map(header => (
                      <TableHead
                        key={header.field}
                        className={`whitespace-normal break-words ${
                          header.field === 'amount' ? 'text-right' : ''
                        } min-w-0`}
                      >
                        <div
                          className={`flex items-center gap-1 min-w-0 ${
                            header.field === 'amount' ? 'justify-end' : ''
                          }`}
                        >
                          <SortableHeader
                            label={header.label}
                            field={header.field}
                            sortField={sortField}
                            sortDirection={sortDirection}
                            onSort={field =>
                              handleSort(field as keyof DisplayTransaction)
                            }
                            align={header.field === 'amount' ? 'right' : 'left'}
                          />
                          {header.field === 'date' && (
                            <ColumnFilterPopover
                              title="Filter by Date"
                              options={dateFilterOptions}
                              selectedValues={dateFilters}
                              onSelectionChange={setDateFilters}
                              searchTerm={dateSearch}
                              onSearchChange={setDateSearch}
                            />
                          )}
                          {header.field === 'description' && (
                            <ColumnFilterPopover
                              title="Filter by Description"
                              options={descriptionFilterOptions}
                              selectedValues={descriptionFilters}
                              onSelectionChange={setDescriptionFilters}
                              searchTerm={descriptionSearch}
                              onSearchChange={setDescriptionSearch}
                            />
                          )}
                          {header.field === 'categoryType' && (
                            <ColumnFilterPopover
                              title="Filter by Type"
                              options={categoryTypeFilterOptions}
                              selectedValues={categoryTypeFilters}
                              onSelectionChange={setCategoryTypeFilters}
                              searchTerm={categoryTypeSearch}
                              onSearchChange={setCategoryTypeSearch}
                            />
                          )}
                          {header.field === 'category' && (
                            <ColumnFilterPopover
                              title="Filter by Category"
                              options={categoryFilterOptions}
                              selectedValues={filterCategories}
                              onSelectionChange={setFilterCategories}
                              searchTerm={categorySearch}
                              onSearchChange={setCategorySearch}
                            />
                          )}
                          {header.field === 'account' && (
                            <ColumnFilterPopover
                              title="Filter by Account"
                              options={accountFilterOptions}
                              selectedValues={accountFilters}
                              onSelectionChange={setAccountFilters}
                              searchTerm={accountSearch}
                              onSearchChange={setAccountSearch}
                            />
                          )}
                          {header.field === 'amount' && (
                            <ColumnFilterPopover
                              title="Filter by Amount"
                              options={amountFilterOptions}
                              selectedValues={amountFilters}
                              onSelectionChange={setAmountFilters}
                              searchTerm={amountSearch}
                              onSearchChange={setAmountSearch}
                            />
                          )}
                        </div>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell
                        colSpan={getTableHeaders().length}
                        className="text-center py-8"
                      >
                        <div className="flex items-center justify-center">
                          <LoadingSpinner />
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    visibleTransactions.map((transaction, index) => (
                      <TableRow
                        key={`${transaction.id}-${index}`}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => openEditModal(transaction)}
                        title="Click to edit"
                      >
                        {getTableHeaders().map(header => (
                          <Fragment key={String(header.field)}>
                            {renderTableCell(transaction, header.field)}
                          </Fragment>
                        ))}
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Infinite scroll sentinel and loading indicator */}
      {hasMore && (
        <div className="flex flex-col items-center py-4">
          <div ref={observerTarget} className="h-4" />
          {loadingMore ? (
            <LoadingSpinner className="h-5 w-5" />
          ) : (
            <p className="text-sm text-muted-foreground">
              Showing {visibleTransactions.length} of{' '}
              {totalCount ?? transactions.length} transactions
            </p>
          )}
        </div>
      )}

      {!hasMore && visibleTransactions.length > 0 && (
        <div className="text-center py-4">
          <p className="text-sm text-muted-foreground">
            Showing all {totalCount ?? visibleTransactions.length} transactions
          </p>
        </div>
      )}

      {visibleTransactions.length === 0 && !loading && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">No transactions found.</p>
          </CardContent>
        </Card>
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedTransaction(null);
        }}
        title="Edit Transaction"
      >
        <TransactionForm
          formData={editFormData}
          onFormChange={setEditFormData}
          onSubmit={handleEditSubmit}
          onDelete={handleDelete}
          accounts={accounts}
          categories={categories}
          submitLabel="Save"
        />
      </Modal>
    </div>
  );
}
