import { AccountHistoryTable } from '@/components/accounts/AccountHistoryTable';
import { AccountTiles } from '@/components/accounts/AccountTiles';
import { TransactionTable } from '@/components/transactions/TransactionTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import {
  DisplayTransaction,
  TransactionTypeFilter,
  transformTransaction,
} from '@/types/transactions';
import { useEffect, useState } from 'react';

// Main DataTable Component
export function DataTable() {
  const { preferences } = usePreferences();
  const [transactions, setTransactions] = useState<DisplayTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'transactions' | 'accounts'>(
    'transactions'
  );
  const [typeFilter, setTypeFilter] = useState<TransactionTypeFilter>('all');
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(
    null
  );

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [transactionsData, categoriesData, accountsData] =
        await Promise.all([
          transactionsApiService.getTransactions({
            type: typeFilter === 'all' ? undefined : typeFilter,
          }),
          transactionsApiService.getCategories(),
          transactionsApiService.getAccounts(),
        ]);

      // Transform and set data
      setTransactions(transactionsData.map(transformTransaction));
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
  }, [typeFilter]);

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
        {/* View toggle and filters */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* View toggle: Transactions / Accounts */}
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant={activeView === 'transactions' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveView('transactions')}
              aria-pressed={activeView === 'transactions'}
            >
              Transactions
            </Button>
            <Button
              type="button"
              variant={activeView === 'accounts' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveView('accounts')}
              aria-pressed={activeView === 'accounts'}
            >
              Accounts
            </Button>
          </div>

          {/* Transaction type filter (only visible in transactions view) */}
          {activeView === 'transactions' && (
            <div className="w-48">
              <Select
                value={typeFilter}
                onValueChange={value =>
                  setTypeFilter(value as TransactionTypeFilter)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Transactions</SelectItem>
                  <SelectItem value="credit">Income (Credit)</SelectItem>
                  <SelectItem value="debit">Expenses (Debit)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Main content */}
        <div className="overflow-x-auto min-w-0">
          {activeView === 'transactions' ? (
            <div className="min-w-0 max-w-full">
              <TransactionTable
                transactions={transactions}
                onTransactionsChange={setTransactions}
                typeFilter={typeFilter}
                accounts={accounts}
                categories={categories}
                loading={loading}
                onRefresh={loadData}
              />
            </div>
          ) : (
            <div className="min-w-0 max-w-full space-y-6">
              <AccountTiles
                accounts={accounts}
                selectedAccountId={selectedAccountId}
                onAccountSelect={setSelectedAccountId}
                currency={preferences.currency || 'USD'}
              />
              <AccountHistoryTable
                accountId={selectedAccountId}
                accounts={accounts}
                onDataChange={loadData}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
