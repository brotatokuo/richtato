import { TransactionTable } from '@/components/transactions/TransactionTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import { DisplayTransaction, transformTransaction } from '@/types/transactions';
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
  const [activeMobileTab, setActiveMobileTab] = useState<'income' | 'expense'>(
    'income'
  );

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
      <div className="min-h-screen bg-background">
        <div className="w-full max-w-full mx-auto min-w-0">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardContent className="text-center py-8">
              <p className="text-red-600 mb-4">Error loading data: {error}</p>
              <Button onClick={loadData} variant="outline">
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full max-w-full mx-auto space-y-8 sm:space-y-12 min-w-0">
        {/* Mobile toggle */}
        <div className="md:hidden flex items-center gap-2">
          <Button
            type="button"
            variant={activeMobileTab === 'income' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveMobileTab('income')}
            aria-pressed={activeMobileTab === 'income'}
          >
            Income
          </Button>
          <Button
            type="button"
            variant={activeMobileTab === 'expense' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveMobileTab('expense')}
            aria-pressed={activeMobileTab === 'expense'}
          >
            Expense
          </Button>
        </div>

        {/* Mobile view: show one table at a time */}
        <div className="md:hidden overflow-x-auto min-w-0">
          {activeMobileTab === 'income' ? (
            <div className="min-w-0 max-w-full">
              <TransactionTable
                type="income"
                transactions={incomeTransactions}
                onTransactionsChange={setIncomeTransactions}
                accounts={accounts}
                categories={categories}
                loading={loading}
                onRefresh={loadData}
              />
            </div>
          ) : (
            <div className="min-w-0 max-w-full">
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
          )}
        </div>

        {/* Desktop/tablet: show both tables stacked */}
        <div className="hidden md:block overflow-x-auto min-w-0">
          {/* Income Table */}
          <div className="min-w-0 max-w-full">
            <TransactionTable
              type="income"
              transactions={incomeTransactions}
              onTransactionsChange={setIncomeTransactions}
              accounts={accounts}
              categories={categories}
              loading={loading}
              onRefresh={loadData}
            />
          </div>
        </div>

        <div className="hidden md:block overflow-x-auto min-w-0">
          {/* Expense Table */}
          <div className="min-w-0 max-w-full">
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
      </div>
    </div>
  );
}
