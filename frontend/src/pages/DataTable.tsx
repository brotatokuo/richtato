import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  ArrowUpDown,
  Calendar,
  CreditCard,
  Download,
  Filter,
  Plus,
  RefreshCw,
  Search,
  Tag,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface TransactionFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
  category?: string;
}

type TransactionType = 'income' | 'expense';

interface FilterOption {
  label: string;
  value: string;
  count: number;
}

interface ContextMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  onClose: () => void;
  options: FilterOption[];
  onSelect: (value: string) => void;
  title: string;
}

interface TransactionTableProps {
  type: TransactionType;
  transactions: DisplayTransaction[];
  onTransactionsChange: (transactions: DisplayTransaction[]) => void;
}

// Display transaction interface (different from API)
interface DisplayTransaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  account: string;
}

// Helper function to transform API transaction to display format
const transformTransaction = (
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

// Context Menu Component
function ContextMenu({
  isOpen,
  position,
  onClose,
  options,
  onSelect,
  title,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-card border border-border rounded-md shadow-lg p-2 min-w-48"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="text-sm font-medium text-muted-foreground mb-2 px-2 py-1">
        {title}
      </div>
      <div className="space-y-1">
        {options.map(option => (
          <button
            key={option.value}
            className="w-full text-left px-2 py-1.5 text-sm hover:bg-muted rounded-sm flex items-center justify-between"
            onClick={() => {
              onSelect(option.value);
              onClose();
            }}
          >
            <span>{option.label}</span>
            <span className="text-xs text-muted-foreground">
              {option.count}
            </span>
          </button>
        ))}
        <button
          className="w-full text-left px-2 py-1.5 text-sm hover:bg-muted rounded-sm text-muted-foreground"
          onClick={() => {
            onSelect('');
            onClose();
          }}
        >
          Clear filter
        </button>
      </div>
    </div>
  );
}

// Reusable Transaction Form Component
function TransactionForm({
  type,
  formData,
  onFormChange,
  onSubmit,
  onCancel,
  accounts,
  categories,
}: {
  type: TransactionType;
  formData: TransactionFormData;
  onFormChange: (data: TransactionFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  accounts: Account[];
  categories: Category[];
}) {
  const isIncome = type === 'income';
  const colorClass = isIncome ? 'green' : 'red';
  const title = isIncome ? 'Income' : 'Expense';
  const placeholder = isIncome
    ? 'e.g., Salary, Freelance work'
    : 'e.g., Groceries, Gas, Coffee';

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-card-foreground">
          Add New {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor={`${type}-description`}>Description</Label>
              <Input
                id={`${type}-description`}
                value={formData.description}
                onChange={e =>
                  onFormChange({
                    ...formData,
                    description: e.target.value,
                  })
                }
                placeholder={placeholder}
                required
              />
            </div>
            <div>
              <Label htmlFor={`${type}-amount`}>Amount</Label>
              <Input
                id={`${type}-amount`}
                type="number"
                step="0.01"
                min="0"
                value={formData.amount}
                onChange={e =>
                  onFormChange({
                    ...formData,
                    amount: e.target.value,
                  })
                }
                placeholder="0.00"
                required
              />
            </div>
            <div>
              <Label htmlFor={`${type}-date`}>Date</Label>
              <Input
                id={`${type}-date`}
                type="date"
                value={formData.date}
                onChange={e =>
                  onFormChange({
                    ...formData,
                    date: e.target.value,
                  })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor={`${type}-account`}>Account</Label>
              <Select
                value={formData.account_name}
                onValueChange={value =>
                  onFormChange({
                    ...formData,
                    account_name: value,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map(account => (
                    <SelectItem key={account.id} value={account.name}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {!isIncome && (
              <div className="md:col-span-2">
                <Label htmlFor={`${type}-category`}>Category</Label>
                <Select
                  value={formData.category || ''}
                  onValueChange={value =>
                    onFormChange({
                      ...formData,
                      category: value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map(category => (
                      <SelectItem key={category.id} value={category.name}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              type="submit"
              className={`bg-${colorClass}-600 hover:bg-${colorClass}-700`}
            >
              Add {title}
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

// Reusable Search and Filter Component
function SearchAndFilter({
  type,
  searchTerm,
  onSearchChange,
  filterCategory,
  onFilterChange,
  categories,
}: {
  type: TransactionType;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  filterCategory: string;
  onFilterChange: (category: string) => void;
  categories: string[];
}) {
  const isIncome = type === 'income';
  const placeholder = isIncome
    ? 'Search income transactions...'
    : 'Search expense transactions...';

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardContent className="p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={placeholder}
                value={searchTerm}
                onChange={e => onSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          {!isIncome && (
            <div className="w-48">
              <Select
                value={filterCategory || 'all'}
                onValueChange={value =>
                  onFilterChange(value === 'all' ? '' : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Reusable Transaction Table Component
function TransactionTable({
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
  const [showAddForm, setShowAddForm] = useState(false);
  const [sortField, setSortField] = useState<keyof DisplayTransaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

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
  const title = isIncome ? 'Income Transactions' : 'Expense Transactions';
  const icon = isIncome ? TrendingUp : TrendingDown;
  const IconComponent = icon;

  const [formData, setFormData] = useState<TransactionFormData>({
    description: '',
    date: new Date().toISOString().split('T')[0],
    amount: '',
    account_name: '',
    ...(isIncome ? {} : { category: '' }),
  });

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

      // Reset form
      setFormData({
        description: '',
        date: new Date().toISOString().split('T')[0],
        amount: '',
        account_name: '',
        ...(isIncome ? {} : { category: '' }),
      });
      setShowAddForm(false);
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
        return <TableCell>{transaction.description}</TableCell>;
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
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full dark:bg-blue-900/20 dark:text-blue-400">
                  <Calendar className="h-3 w-3" />
                  {new Date(dateFilter).toLocaleDateString()}
                </span>
              )}
              {!isIncome && filterCategory && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full dark:bg-purple-900/20 dark:text-purple-400">
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
                }}
                className="text-xs h-6 px-2"
              >
                Clear all
              </Button>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={onRefresh} variant="outline" disabled={loading}>
            <RefreshCw
              className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
          <Button
            onClick={() => setShowAddForm(!showAddForm)}
            className={`bg-${colorClass}-600 hover:bg-${colorClass}-700`}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add {isIncome ? 'Income' : 'Expense'}
          </Button>
        </div>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <TransactionForm
          type={type}
          formData={formData}
          onFormChange={setFormData}
          onSubmit={handleSubmit}
          onCancel={() => setShowAddForm(false)}
          accounts={accounts}
          categories={categories}
        />
      )}

      {/* Search and Filters */}
      <SearchAndFilter
        type={type}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        filterCategory={filterCategory}
        onFilterChange={setFilterCategory}
        categories={categoryNames}
      />

      {/* Table */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                {getTableHeaders().map(header => (
                  <TableHead
                    key={header.field}
                    className={`cursor-pointer hover:bg-muted/50 ${
                      header.field === 'amount' ? 'text-right' : ''
                    }`}
                    onClick={() =>
                      handleSort(header.field as keyof DisplayTransaction)
                    }
                    onContextMenu={
                      header.filterable
                        ? e => handleContextMenu(e, header.field, header.label)
                        : undefined
                    }
                  >
                    <div
                      className={`flex items-center gap-2 ${
                        header.field === 'amount' ? 'justify-end' : ''
                      }`}
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
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Loading transactions...
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredTransactions.map((transaction, index) => (
                  <TableRow key={`${transaction.id}-${index}`}>
                    {getTableHeaders().map(header =>
                      renderTableCell(transaction, header.field)
                    )}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {filteredTransactions.length === 0 && (
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

// Main DataTable Component
export function DataTable() {
  const [incomeTransactions, setIncomeTransactions] = useState<
    DisplayTransaction[]
  >([]);
  const [expenseTransactions, setExpenseTransactions] = useState<
    DisplayTransaction[]
  >([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [incomeData, expenseData, accountsData, categoriesData] =
        await Promise.all([
          transactionsApiService.getIncomeTransactions(),
          transactionsApiService.getExpenseTransactions(),
          transactionsApiService.getAccounts(),
          transactionsApiService.getCategories(),
        ]);

      // Transform and set data
      setIncomeTransactions(incomeData.map(transformTransaction));
      setExpenseTransactions(expenseData.map(transformTransaction));
      setAccounts(accountsData);
      setCategories(categoriesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardContent className="text-center py-8">
              <p className="text-red-600 mb-4">Error loading data: {error}</p>
              <Button onClick={loadData} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Income Table */}
        <TransactionTable
          type="income"
          transactions={incomeTransactions}
          onTransactionsChange={setIncomeTransactions}
          accounts={accounts}
          categories={categories}
          loading={loading}
          onRefresh={loadData}
        />

        {/* Expense Table */}
        <TransactionTable
          type="expense"
          transactions={expenseTransactions}
          onTransactionsChange={setExpenseTransactions}
          accounts={accounts}
          categories={categories}
          loading={loading}
          onRefresh={loadData}
        />
      </div>
    </div>
  );
}
