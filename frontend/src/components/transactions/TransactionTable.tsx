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
  Tag,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useState } from 'react';

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
  const [sortField, setSortField] = useState<keyof DisplayTransaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    isOpen: boolean;
    position: { x: number; y: number };
    field: string;
    title: string;
  }>({
    isOpen: false,
    position: { x: 0, y: 0 },
    field: '',
    title: '',
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
    date: new Date().toISOString().split('T')[0],
    amount: '',
    account_name: '',
    ...(isIncome ? {} : { category: '' }),
  });

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
        date: new Date().toISOString().split('T')[0],
        amount: '',
        account_name: '',
        ...(isIncome ? {} : { category: '' }),
      });
      setShowAddModal(false);
    } catch (error) {
      console.error('Error creating transaction:', error);
      // You might want to show a toast notification here
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
                      <TableRow key={`${transaction.id}-${index}`}>
                        {getTableHeaders().map(header =>
                          renderTableCell(transaction, header.field)
                        )}
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
    </div>
  );
}
