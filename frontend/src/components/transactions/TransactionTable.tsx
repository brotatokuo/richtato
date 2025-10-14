import { SearchAndFilter } from '@/components/transactions/SearchAndFilter';
import { TransactionForm } from '@/components/transactions/TransactionForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ContextMenu } from '@/components/ui/ContextMenu';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Account,
  Category,
  Transaction,
  transactionsApiService,
} from '@/lib/api/transactions';
import {
  DisplayTransaction,
  FilterOption,
  TransactionFormData,
  TransactionTableProps,
  transformTransaction,
} from '@/types/transactions';
import {
  ArrowUpDown,
  Calendar,
  CreditCard,
  Filter,
  Plus,
  ScanLine,
  Tag,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { Fragment, useEffect, useRef, useState } from 'react';

const getLocalDateString = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export function TransactionTable({
  type,
  transactions,
  onTransactionsChange,
  accounts,
  categories,
  loading,
  onRefresh,
}: TransactionTableProps & {
  accounts: Account[];
  categories: Category[];
  loading: boolean;
  onRefresh: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [sortField, setSortField] = useState<keyof DisplayTransaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Context menu state
  const [contextMenu, setContextMenu] = useState({
    isOpen: false,
    position: { x: 0, y: 0 },
    field: '',
    title: '',
  } as {
    isOpen: boolean;
    position: { x: number; y: number };
    field: string;
    title: string;
  });

  // Additional filters
  const [dateFilter, setDateFilter] = useState('');
  const [accountFilter, setAccountFilter] = useState('');

  const isIncome = type === 'income';
  const colorClass = isIncome ? 'green' : 'red';
  const title = isIncome ? 'Income' : 'Expense';
  const icon = isIncome ? TrendingUp : TrendingDown;
  const IconComponent = icon;

  const [formData, setFormData] = useState<TransactionFormData>({
    description: '',
    date: getLocalDateString(),
    amount: '',
    account_name: '',
    ...(isIncome ? {} : { category: '' }),
  });

  // Edit modal state
  const [selectedTransaction, setSelectedTransaction] =
    useState<DisplayTransaction | null>(null);
  const [editFormData, setEditFormData] = useState<TransactionFormData>({
    description: '',
    date: getLocalDateString(),
    amount: '',
    account_name: '',
    ...(isIncome ? {} : { category: '' }),
  });

  // Receipt modal state
  const [receiptAccountId, setReceiptAccountId] = useState<number | ''>('');
  const [receiptCategoryId, setReceiptCategoryId] = useState<number | ''>('');
  const [receiptDate, setReceiptDate] = useState<string>(getLocalDateString());
  const receiptFileRef = useRef<HTMLInputElement | null>(null);

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterCategory, dateFilter, accountFilter]);

  const filteredTransactions = transactions
    .filter(transaction => {
      const matchesSearch =
        transaction.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        transaction.account.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (isIncome
          ? false
          : transaction.category
              .toLowerCase()
              .includes(searchTerm.toLowerCase()));
      const matchesCategory =
        isIncome || !filterCategory || transaction.category === filterCategory;
      const matchesDate = !dateFilter || transaction.date === dateFilter;
      const matchesAccount =
        !accountFilter || transaction.account === accountFilter;
      return matchesSearch && matchesCategory && matchesDate && matchesAccount;
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

  // Pagination calculations
  const totalItems = filteredTransactions.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = filteredTransactions.slice(
    startIndex,
    endIndex
  );

  const categoryNames = Array.from(new Set(transactions.map(t => t.category)));

  // Generate filter options for context menu
  const getFilterOptions = (field: string): FilterOption[] => {
    switch (field) {
      case 'date':
        const dates = Array.from(new Set(transactions.map(t => t.date)))
          .sort()
          .reverse(); // Most recent first
        return dates.map(date => ({
          label: new Date(date).toLocaleDateString(),
          value: date,
          count: transactions.filter(t => t.date === date).length,
        }));
      case 'category':
        return categoryNames.map(category => ({
          label: category,
          value: category,
          count: transactions.filter(t => t.category === category).length,
        }));
      case 'account':
        const accountNames = Array.from(
          new Set(transactions.map(t => t.account))
        );
        return accountNames.map(account => ({
          label: account,
          value: account,
          count: transactions.filter(t => t.account === account).length,
        }));
      default:
        return [];
    }
  };

  const handleContextMenu = (
    e: React.MouseEvent,
    field: string,
    title: string
  ) => {
    e.preventDefault();
    setContextMenu({
      isOpen: true,
      position: { x: e.clientX, y: e.clientY },
      field,
      title,
    });
  };

  const handleFilterSelect = (value: string) => {
    switch (contextMenu.field) {
      case 'date':
        setDateFilter(value);
        break;
      case 'category':
        setFilterCategory(value);
        break;
      case 'account':
        setAccountFilter(value);
        break;
    }
  };

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
    if (
      !formData.description ||
      !formData.amount ||
      !formData.account_name ||
      (!isIncome && !formData.category)
    ) {
      return;
    }

    try {
      // Find the account ID
      const account = accounts.find(acc => acc.name === formData.account_name);
      if (!account) {
        throw new Error('Account not found');
      }

      // Find the category ID for expenses
      let categoryId: number | undefined;
      if (!isIncome && formData.category) {
        const category = categories.find(cat => cat.name === formData.category);
        if (!category) {
          throw new Error('Category not found');
        }
        categoryId = category.id;
      }

      const transactionData = {
        description: formData.description,
        date: formData.date,
        amount: parseFloat(formData.amount),
        Account: account.name,
        ...(categoryId && {
          Category: categories.find(cat => cat.id === categoryId)?.name,
        }),
      };

      let newTransaction: Transaction;
      if (isIncome) {
        newTransaction =
          await transactionsApiService.createIncomeTransaction(transactionData);
      } else {
        newTransaction =
          await transactionsApiService.createExpenseTransaction(
            transactionData
          );
      }

      // Transform and add to local state
      const transformedTransaction = transformTransaction(newTransaction);
      onTransactionsChange([transformedTransaction, ...transactions]);

      // Reset form and close modal
      setFormData({
        description: '',
        date: getLocalDateString(),
        amount: '',
        account_name: '',
        ...(isIncome ? {} : { category: '' }),
      });
      setShowAddModal(false);
      onRefresh();
    } catch (error) {
      console.error('Error creating transaction:', error);
      // You might want to show a toast notification here
    }
  };

  const handleReceiptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const file = receiptFileRef.current?.files?.[0];
      if (!file) return;

      if (!receiptAccountId || typeof receiptAccountId !== 'number') {
        throw new Error('Please select an account');
      }

      const created =
        await transactionsApiService.uploadReceiptAndCreateExpense({
          file,
          accountId: receiptAccountId,
          categoryId:
            !isIncome && typeof receiptCategoryId === 'number'
              ? receiptCategoryId
              : undefined,
        });

      const transformedTransaction = transformTransaction(created as any);
      onTransactionsChange([transformedTransaction, ...transactions]);

      // reset
      if (receiptFileRef.current) receiptFileRef.current.value = '';
      setReceiptAccountId('');
      setReceiptCategoryId('');
      setReceiptDate(getLocalDateString());
      setShowReceiptModal(false);
      onRefresh();
    } catch (error) {
      console.error('Error uploading receipt:', error);
    }
  };

  const openEditModal = (t: DisplayTransaction) => {
    setSelectedTransaction(t);
    setEditFormData({
      description: t.description,
      date: t.date,
      amount: Math.abs(t.amount).toString(),
      account_name: t.account,
      ...(isIncome ? {} : { category: t.category || '' }),
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransaction) return;
    try {
      const account = accounts.find(
        acc => acc.name === editFormData.account_name
      );
      if (!account) throw new Error('Account not found');

      let payload: any;
      if (isIncome) {
        // Income expects Account as primary key id
        payload = {
          description: editFormData.description,
          date: editFormData.date,
          amount: parseFloat(editFormData.amount),
          Account: account.id,
        };
      } else {
        // Expense expects account_name (id) and optional category (id)
        const categoryId = editFormData.category
          ? categories.find(cat => cat.name === editFormData.category)?.id
          : undefined;
        payload = {
          description: editFormData.description,
          date: editFormData.date,
          amount: parseFloat(editFormData.amount),
          account_name: account.id,
          ...(categoryId !== undefined ? { category: categoryId } : {}),
        };
      }

      const idNum = Number(selectedTransaction.id);
      let updated: Transaction;
      if (isIncome) {
        updated = await transactionsApiService.updateIncomeTransaction(
          idNum,
          payload
        );
      } else {
        updated = await transactionsApiService.updateExpenseTransaction(
          idNum,
          payload
        );
      }

      // Enrich with names for consistent display mapping
      const enriched = (
        isIncome
          ? { ...updated, Account: account.name }
          : {
              ...updated,
              Account: account.name,
              Category: editFormData.category || selectedTransaction.category,
            }
      ) as any;
      const transformed = transformTransaction(enriched);
      const next = transactions.map(t =>
        t.id === selectedTransaction.id ? transformed : t
      );
      onTransactionsChange(next);

      setShowEditModal(false);
      setSelectedTransaction(null);
      onRefresh();
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
      if (isIncome) {
        await transactionsApiService.deleteIncomeTransaction(idNum);
      } else {
        await transactionsApiService.deleteExpenseTransaction(idNum);
      }
      const next = transactions.filter(t => t.id !== selectedTransaction.id);
      onTransactionsChange(next);
      setShowEditModal(false);
      setSelectedTransaction(null);
      onRefresh();
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

  const getTableHeaders = () => {
    const baseHeaders = [
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
        field: 'account' as keyof DisplayTransaction,
        label: 'Account',
        filterable: true,
      },
    ];

    if (!isIncome) {
      baseHeaders.splice(2, 0, {
        field: 'category' as keyof DisplayTransaction,
        label: 'Category',
        filterable: true,
      });
    }

    baseHeaders.push({
      field: 'amount' as keyof DisplayTransaction,
      label: 'Amount',
      filterable: false,
    });

    return baseHeaders;
  };

  const renderTableCell = (
    transaction: DisplayTransaction,
    field: keyof DisplayTransaction
  ) => {
    switch (field) {
      case 'date':
        return (
          <TableCell className="font-medium">
            {new Date(transaction.date).toLocaleDateString()}
          </TableCell>
        );
      case 'description':
        return (
          <TableCell className="whitespace-normal break-words break-all">
            {transaction.description}
          </TableCell>
        );
      case 'account':
        return <TableCell>{transaction.account}</TableCell>;
      case 'category':
        return (
          <TableCell>
            <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
              {transaction.category}
            </span>
          </TableCell>
        );
      case 'amount':
        const amount = Math.abs(transaction.amount);
        const sign = isIncome ? '+' : '-';
        const color = isIncome ? 'text-green-600' : 'text-red-600';
        return (
          <TableCell className={`text-right font-medium ${color}`}>
            {sign}${amount.toFixed(2)}
          </TableCell>
        );
      default:
        return <TableCell>{String(transaction[field])}</TableCell>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground flex items-center gap-2">
            <IconComponent className={`h-6 w-6 text-${colorClass}-600`} />
            {title}
          </h2>
          {/* Active filters indicator */}
          {(dateFilter || accountFilter || (!isIncome && filterCategory)) && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm text-muted-foreground">
                Active filters:
              </span>
              {dateFilter && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-primary/15 text-primary text-xs rounded-full dark:bg-primary/20 dark:text-primary">
                  <Calendar className="h-3 w-3" />
                  {new Date(dateFilter).toLocaleDateString()}
                </span>
              )}
              {!isIncome && filterCategory && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded-full dark:bg-secondary/20 dark:text-secondary-foreground">
                  <Tag className="h-3 w-3" />
                  {filterCategory}
                </span>
              )}
              {accountFilter && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full dark:bg-green-900/20 dark:text-green-400">
                  <CreditCard className="h-3 w-3" />
                  {accountFilter}
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setDateFilter('');
                  setAccountFilter('');
                  setFilterCategory('');
                  setCurrentPage(1);
                }}
                className="text-xs h-6 px-2"
              >
                Clear all
              </Button>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {!isIncome && (
            <Button onClick={() => setShowReceiptModal(true)} variant="outline">
              <ScanLine className="h-4 w-4 mr-2" />
              Scan/Upload Receipt
            </Button>
          )}
          <Button onClick={() => setShowAddModal(true)} variant="default">
            <Plus className="h-4 w-4 mr-2" />
            Add {isIncome ? 'Income' : 'Expense'}
          </Button>
        </div>
      </div>

      {/* Add Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title={`Add New ${isIncome ? 'Income' : 'Expense'}`}
      >
        <TransactionForm
          type={type}
          formData={formData}
          onFormChange={setFormData}
          onSubmit={handleSubmit}
          onCancel={() => setShowAddModal(false)}
          accounts={accounts}
          categories={categories}
        />
      </Modal>

      {/* Receipt Modal */}
      <Modal
        isOpen={showReceiptModal}
        onClose={() => setShowReceiptModal(false)}
        title="Scan/Upload Receipt"
      >
        <form onSubmit={handleReceiptSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label
                className="block text-sm font-medium mb-1"
                htmlFor="receipt-file"
              >
                Receipt file
              </label>
              <input
                id="receipt-file"
                ref={receiptFileRef}
                type="file"
                accept="image/*,.pdf"
                capture="environment"
                className="block w-full text-sm"
                required
              />
            </div>
            <div>
              <label
                className="block text-sm font-medium mb-1"
                htmlFor="receipt-account"
              >
                Account
              </label>
              <select
                id="receipt-account"
                value={receiptAccountId}
                onChange={e =>
                  setReceiptAccountId(
                    e.target.value ? Number(e.target.value) : ''
                  )
                }
                className="block w-full border rounded px-2 py-2 text-sm"
                required
              >
                <option value="">Select account</option>
                {accounts.map(acc => (
                  <option key={acc.id} value={acc.id}>
                    {acc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                className="block text-sm font-medium mb-1"
                htmlFor="receipt-category"
              >
                Category (optional)
              </label>
              <select
                id="receipt-category"
                value={receiptCategoryId}
                onChange={e =>
                  setReceiptCategoryId(
                    e.target.value ? Number(e.target.value) : ''
                  )
                }
                className="block w-full border rounded px-2 py-2 text-sm"
              >
                <option value="">Auto or Unknown</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                className="block text-sm font-medium mb-1"
                htmlFor="receipt-date"
              >
                Date
              </label>
              <input
                id="receipt-date"
                type="date"
                value={receiptDate}
                onChange={e => setReceiptDate(e.target.value)}
                className="block w-full border rounded px-2 py-2 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              type="submit"
              className={`bg-${colorClass}-600 hover:bg-${colorClass}-700`}
            >
              Create Expense from Receipt
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowReceiptModal(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* Search and Filters */}
      <SearchAndFilter
        type={type}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        filterCategory={filterCategory}
        onFilterChange={setFilterCategory}
        categories={categoryNames}
      />

      {/* Mobile list (<= md) */}
      <div className="md:hidden">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-0">
            {loading ? (
              <div className="py-8 text-center text-sm">
                Loading transactions...
              </div>
            ) : (
              <div className="divide-y">
                {paginatedTransactions.map((t, index) => {
                  const amount = Math.abs(t.amount);
                  const sign = isIncome ? '+' : '-';
                  const color = isIncome ? 'text-green-600' : 'text-red-600';
                  return (
                    <div
                      key={`${t.id}-${index}`}
                      className="p-4 w-full flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between"
                    >
                      <div className="space-y-1 min-w-0 sm:pr-2">
                        <div className="text-sm font-medium whitespace-normal break-words">
                          {t.description}
                        </div>
                        <div className="text-xs text-muted-foreground whitespace-normal break-words">
                          {new Date(t.date).toLocaleDateString()} • {t.account}
                          {!isIncome && t.category ? ` • ${t.category}` : ''}
                        </div>
                      </div>
                      <div
                        className={`sm:ml-4 sm:text-right text-sm font-semibold ${color}`}
                      >
                        {sign}${amount.toFixed(2)}
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
                        className={`cursor-pointer hover:bg-muted/50 whitespace-normal break-words ${
                          header.field === 'amount' ? 'text-right' : ''
                        } min-w-0`}
                        onClick={() =>
                          handleSort(header.field as keyof DisplayTransaction)
                        }
                        onContextMenu={
                          header.filterable
                            ? e =>
                                handleContextMenu(e, header.field, header.label)
                            : undefined
                        }
                      >
                        <div
                          className={`flex items-center gap-2 min-w-0 ${
                            header.field === 'amount' ? 'justify-end' : ''
                          } flex-wrap`}
                        >
                          {header.label}
                          <div className="flex items-center gap-1">
                            {header.filterable && (
                              <Filter className="h-3 w-3 text-muted-foreground" />
                            )}
                            <ArrowUpDown className="h-4 w-4" />
                          </div>
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
                        <div className="flex items-center justify-center gap-2">
                          Loading transactions...
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedTransactions.map((transaction, index) => (
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

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
      />

      {totalItems === 0 && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">
              No {isIncome ? 'income' : 'expense'} transactions found.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Context Menu */}
      <ContextMenu
        isOpen={contextMenu.isOpen}
        position={contextMenu.position}
        onClose={() => setContextMenu(prev => ({ ...prev, isOpen: false }))}
        options={getFilterOptions(contextMenu.field)}
        onSelect={handleFilterSelect}
        title={contextMenu.title}
      />

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedTransaction(null);
        }}
        title={`Edit ${isIncome ? 'Income' : 'Expense'}`}
      >
        <TransactionForm
          type={type}
          formData={editFormData}
          onFormChange={setEditFormData}
          onSubmit={handleEditSubmit}
          onCancel={() => {
            setShowEditModal(false);
            setSelectedTransaction(null);
          }}
          accounts={accounts}
          categories={categories}
          submitLabel="Save changes"
        />
        <div className="mt-4">
          <Button
            type="button"
            variant="outline"
            className="text-red-600 border-red-600 hover:bg-red-50"
            onClick={handleDelete}
          >
            Delete {isIncome ? 'Income' : 'Expense'}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
