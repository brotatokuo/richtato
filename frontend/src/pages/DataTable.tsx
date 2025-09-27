import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Download, Search } from 'lucide-react';
import { useState } from 'react';

interface Transaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  account: string;
}

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

export function DataTable() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');

  const filteredTransactions = mockTransactions.filter(transaction => {
    const matchesSearch =
      transaction.description
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      transaction.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory =
      !filterCategory || transaction.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(new Set(mockTransactions.map(t => t.category)));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Transaction Data</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div className="w-48">
          <select
            value={filterCategory}
            onChange={e => setFilterCategory(e.target.value)}
            className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Account</TableHead>
              <TableHead className="text-right">Amount</TableHead>
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
                  <span className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
                    {transaction.category}
                  </span>
                </TableCell>
                <TableCell>{transaction.account}</TableCell>
                <TableCell
                  className={`text-right font-medium ${
                    transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {transaction.amount >= 0 ? '+' : ''}$
                  {Math.abs(transaction.amount).toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {filteredTransactions.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No transactions found matching your criteria.
        </div>
      )}
    </div>
  );
}
