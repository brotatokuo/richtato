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
  ArrowUpDown,
  Download,
  Plus,
  Search,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useState } from 'react';

interface Transaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  account: string;
}

interface IncomeFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
}

interface ExpenseFormData {
  description: string;
  date: string;
  amount: string;
  account_name: string;
  category: string;
}

interface Account {
  id: string;
  name: string;
  type: 'checking' | 'savings' | 'credit_card' | 'investment';
}

interface Category {
  id: string;
  name: string;
}

const mockAccounts: Account[] = [
  { id: '1', name: 'Checking Account', type: 'checking' },
  { id: '2', name: 'Savings Account', type: 'savings' },
  { id: '3', name: 'Credit Card', type: 'credit_card' },
  { id: '4', name: 'Investment Account', type: 'investment' },
];

const mockCategories: Category[] = [
  { id: '1', name: 'Food & Dining' },
  { id: '2', name: 'Transportation' },
  { id: '3', name: 'Entertainment' },
  { id: '4', name: 'Utilities' },
  { id: '5', name: 'Healthcare' },
  { id: '6', name: 'Shopping' },
  { id: '7', name: 'Education' },
  { id: '8', name: 'Travel' },
];

const mockTransactions: Transaction[] = [
  {
    id: '1',
    date: '2024-01-15',
    description: 'Grocery Store',
    category: 'Food & Dining',
    amount: -85.5,
    account: 'Checking',
  },
  {
    id: '2',
    date: '2024-01-14',
    description: 'Salary Deposit',
    category: 'Income',
    amount: 3500.0,
    account: 'Checking',
  },
  {
    id: '3',
    date: '2024-01-13',
    description: 'Gas Station',
    category: 'Transportation',
    amount: -45.2,
    account: 'Credit Card',
  },
  {
    id: '4',
    date: '2024-01-12',
    description: 'Coffee Shop',
    category: 'Food & Dining',
    amount: -4.75,
    account: 'Credit Card',
  },
  {
    id: '5',
    date: '2024-01-11',
    description: 'Investment Transfer',
    category: 'Investment',
    amount: -500.0,
    account: 'Savings',
  },
];

// Income Table Component
function IncomeTable() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [sortField, setSortField] = useState<keyof Transaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const [incomeForm, setIncomeForm] = useState<IncomeFormData>({
    description: '',
    date: new Date().toISOString().split('T')[0],
    amount: '',
    account_name: '',
  });

  const [transactions, setTransactions] = useState<Transaction[]>(
    mockTransactions.filter(t => t.amount > 0)
  );

  const filteredTransactions = transactions
    .filter(
      transaction =>
        transaction.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        transaction.account.toLowerCase().includes(searchTerm.toLowerCase())
    )
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

  const handleSort = (field: keyof Transaction) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleIncomeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !incomeForm.description ||
      !incomeForm.amount ||
      !incomeForm.account_name
    ) {
      return;
    }

    const newTransaction: Transaction = {
      id: Date.now().toString(),
      date: incomeForm.date,
      description: incomeForm.description,
      category: 'Income',
      amount: parseFloat(incomeForm.amount),
      account: incomeForm.account_name,
    };

    setTransactions(prev => [newTransaction, ...prev]);
    setIncomeForm({
      description: '',
      date: new Date().toISOString().split('T')[0],
      amount: '',
      account_name: '',
    });
    setShowAddForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-green-600" />
            Income Transactions
          </h2>
          <p className="text-muted-foreground">Track your income sources</p>
        </div>
        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-green-600 hover:bg-green-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Income
        </Button>
      </div>

      {/* Add Income Form */}
      {showAddForm && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-card-foreground">
              Add New Income
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleIncomeSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="income-description">Description</Label>
                  <Input
                    id="income-description"
                    value={incomeForm.description}
                    onChange={e =>
                      setIncomeForm(prev => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    placeholder="e.g., Salary, Freelance work"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="income-amount">Amount</Label>
                  <Input
                    id="income-amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={incomeForm.amount}
                    onChange={e =>
                      setIncomeForm(prev => ({
                        ...prev,
                        amount: e.target.value,
                      }))
                    }
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="income-date">Date</Label>
                  <Input
                    id="income-date"
                    type="date"
                    value={incomeForm.date}
                    onChange={e =>
                      setIncomeForm(prev => ({
                        ...prev,
                        date: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="income-account">Account</Label>
                  <Select
                    value={incomeForm.account_name}
                    onValueChange={value =>
                      setIncomeForm(prev => ({
                        ...prev,
                        account_name: value,
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockAccounts.map(account => (
                        <SelectItem key={account.id} value={account.name}>
                          {account.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700"
                >
                  Add Income
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search income transactions..."
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Income Table */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center gap-2">
                    Date
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('description')}
                >
                  <div className="flex items-center gap-2">
                    Description
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('account')}
                >
                  <div className="flex items-center gap-2">
                    Account
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="text-right cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('amount')}
                >
                  <div className="flex items-center justify-end gap-2">
                    Amount
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransactions.map(transaction => (
                <TableRow key={transaction.id}>
                  <TableCell className="font-medium">
                    {new Date(transaction.date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{transaction.description}</TableCell>
                  <TableCell>{transaction.account}</TableCell>
                  <TableCell className="text-right font-medium text-green-600">
                    +${transaction.amount.toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {filteredTransactions.length === 0 && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">
              No income transactions found.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Expense Table Component
function ExpenseTable() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [sortField, setSortField] = useState<keyof Transaction>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const [expenseForm, setExpenseForm] = useState<ExpenseFormData>({
    description: '',
    date: new Date().toISOString().split('T')[0],
    amount: '',
    account_name: '',
    category: '',
  });

  const [transactions, setTransactions] = useState<Transaction[]>(
    mockTransactions.filter(t => t.amount < 0)
  );

  const filteredTransactions = transactions
    .filter(transaction => {
      const matchesSearch =
        transaction.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        transaction.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        transaction.account.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory =
        !filterCategory || transaction.category === filterCategory;
      return matchesSearch && matchesCategory;
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

  const categories = Array.from(new Set(transactions.map(t => t.category)));

  const handleSort = (field: keyof Transaction) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleExpenseSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !expenseForm.description ||
      !expenseForm.amount ||
      !expenseForm.account_name ||
      !expenseForm.category
    ) {
      return;
    }

    const newTransaction: Transaction = {
      id: Date.now().toString(),
      date: expenseForm.date,
      description: expenseForm.description,
      category: expenseForm.category,
      amount: -parseFloat(expenseForm.amount), // Negative for expenses
      account: expenseForm.account_name,
    };

    setTransactions(prev => [newTransaction, ...prev]);
    setExpenseForm({
      description: '',
      date: new Date().toISOString().split('T')[0],
      amount: '',
      account_name: '',
      category: '',
    });
    setShowAddForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground flex items-center gap-2">
            <TrendingDown className="h-6 w-6 text-red-600" />
            Expense Transactions
          </h2>
          <p className="text-muted-foreground">Track your spending</p>
        </div>
        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-red-600 hover:bg-red-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Expense
        </Button>
      </div>

      {/* Add Expense Form */}
      {showAddForm && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-card-foreground">
              Add New Expense
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleExpenseSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="expense-description">Description</Label>
                  <Input
                    id="expense-description"
                    value={expenseForm.description}
                    onChange={e =>
                      setExpenseForm(prev => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    placeholder="e.g., Groceries, Gas, Coffee"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="expense-amount">Amount</Label>
                  <Input
                    id="expense-amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={expenseForm.amount}
                    onChange={e =>
                      setExpenseForm(prev => ({
                        ...prev,
                        amount: e.target.value,
                      }))
                    }
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="expense-date">Date</Label>
                  <Input
                    id="expense-date"
                    type="date"
                    value={expenseForm.date}
                    onChange={e =>
                      setExpenseForm(prev => ({
                        ...prev,
                        date: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="expense-account">Account</Label>
                  <Select
                    value={expenseForm.account_name}
                    onValueChange={value =>
                      setExpenseForm(prev => ({
                        ...prev,
                        account_name: value,
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockAccounts.map(account => (
                        <SelectItem key={account.id} value={account.name}>
                          {account.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="expense-category">Category</Label>
                  <Select
                    value={expenseForm.category}
                    onValueChange={value =>
                      setExpenseForm(prev => ({
                        ...prev,
                        category: value,
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockCategories.map(category => (
                        <SelectItem key={category.id} value={category.name}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit" className="bg-red-600 hover:bg-red-700">
                  Add Expense
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search expense transactions..."
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-48">
              <Select
                value={filterCategory || 'all'}
                onValueChange={value =>
                  setFilterCategory(value === 'all' ? '' : value)
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
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Expense Table */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center gap-2">
                    Date
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('description')}
                >
                  <div className="flex items-center gap-2">
                    Description
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('category')}
                >
                  <div className="flex items-center gap-2">
                    Category
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('account')}
                >
                  <div className="flex items-center gap-2">
                    Account
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead
                  className="text-right cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('amount')}
                >
                  <div className="flex items-center justify-end gap-2">
                    Amount
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransactions.map(transaction => (
                <TableRow key={transaction.id}>
                  <TableCell className="font-medium">
                    {new Date(transaction.date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{transaction.description}</TableCell>
                  <TableCell>
                    <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                      {transaction.category}
                    </span>
                  </TableCell>
                  <TableCell>{transaction.account}</TableCell>
                  <TableCell className="text-right font-medium text-red-600">
                    -${Math.abs(transaction.amount).toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {filteredTransactions.length === 0 && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">
              No expense transactions found.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Main DataTable Component
export function DataTable() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-white dark:via-slate-200 dark:to-white bg-clip-text text-transparent mb-4">
            Transaction Management
          </h1>
          <p className="text-muted-foreground text-lg">
            Track your income and expenses separately
          </p>
        </div>

        {/* Income Table */}
        <IncomeTable />

        {/* Expense Table */}
        <ExpenseTable />
      </div>
    </div>
  );
}
