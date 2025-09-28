import { TransactionTable } from '@/components/transactions/TransactionTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import { DisplayTransaction, transformTransaction } from '@/types/transactions';
import { RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

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
