import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import {
  AlertCircle,
  Building2,
  CreditCard,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface AccountWithBalance extends Account {
  balance: number;
  lastUpdated: string;
}

const getAccountIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case 'checking':
    case 'checking_account':
      return <Building2 className="h-5 w-5" />;
    case 'savings':
    case 'savings_account':
      return <PiggyBank className="h-5 w-5" />;
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return <TrendingUp className="h-5 w-5" />;
    case 'retirement':
    case '401k':
    case 'ira':
      return <TrendingUp className="h-5 w-5" />;
    case 'credit':
    case 'credit_card':
      return <CreditCard className="h-5 w-5" />;
    case 'cash':
    case 'wallet':
      return <Wallet className="h-5 w-5" />;
    default:
      return <AlertCircle className="h-5 w-5" />;
  }
};

const getAccountTypeColor = (type: string) => {
  switch (type.toLowerCase()) {
    case 'checking':
    case 'checking_account':
      return 'bg-primary';
    case 'savings':
    case 'savings_account':
      return 'bg-green-500';
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return 'bg-secondary';
    case 'retirement':
    case '401k':
    case 'ira':
      return 'bg-orange-500';
    case 'credit':
    case 'credit_card':
      return 'bg-red-500';
    case 'cash':
    case 'wallet':
      return 'bg-yellow-500';
    default:
      return 'bg-gray-500';
  }
};

const getAccountTypeLabel = (type: string) => {
  switch (type.toLowerCase()) {
    case 'checking':
    case 'checking_account':
      return 'Checking Accounts';
    case 'savings':
    case 'savings_account':
      return 'Savings Accounts';
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return 'Investment Accounts';
    case 'retirement':
    case '401k':
    case 'ira':
      return 'Retirement Accounts';
    case 'credit':
    case 'credit_card':
      return 'Credit Cards';
    case 'cash':
    case 'wallet':
      return 'Cash & Wallet';
    default:
      return 'Other Accounts';
  }
};

export function AccountsSection() {
  const [accounts, setAccounts] = useState<AccountWithBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAccounts = async () => {
      try {
        setLoading(true);
        setError(null);

        const accountsData = await transactionsApiService.getAccounts();

        // Transform API data to include mock balance and lastUpdated for now
        // In a real app, these would come from the API
        const accountsWithBalance: AccountWithBalance[] = accountsData.map(
          account => ({
            ...account,
            balance: Math.random() * 50000, // Mock balance - replace with real data
            lastUpdated: new Date().toISOString().split('T')[0], // Mock date
          })
        );

        setAccounts(accountsWithBalance);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load accounts'
        );
      } finally {
        setLoading(false);
      }
    };

    loadAccounts();
  }, []);

  const groupedAccounts = accounts.reduce(
    (acc, account) => {
      if (!acc[account.type]) {
        acc[account.type] = [];
      }
      acc[account.type].push(account);
      return acc;
    },
    {} as Record<string, AccountWithBalance[]>
  );

  // Calculate totals for each account type
  const accountTypeTotals = Object.entries(groupedAccounts).map(
    ([type, accounts]) => ({
      type,
      total: accounts.reduce((sum, account) => sum + account.balance, 0),
      count: accounts.length,
    })
  );

  // Calculate grand total
  const grandTotal = accountTypeTotals.reduce(
    (sum, { total }) => sum + total,
    0
  );

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading accounts...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (accounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">No accounts found</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Accounts</span>
          <span className="text-sm font-normal text-muted-foreground">
            {accounts.length} account{accounts.length !== 1 ? 's' : ''}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          {/* Grand Total Summary */}
          <div className="p-6 border rounded-lg bg-gradient-to-r from-primary/5 to-indigo-50 dark:from-primary/10 dark:to-indigo-950/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  Total Assets
                </h3>
                <p className="text-sm text-muted-foreground">
                  Across all {accounts.length} account
                  {accounts.length !== 1 ? 's' : ''}
                </p>
              </div>
              <div className="text-right">
                <p
                  className={`text-3xl font-bold ${
                    grandTotal >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {grandTotal >= 0 ? '+' : ''}$
                  {Math.abs(grandTotal).toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  {accountTypeTotals.length} account type
                  {accountTypeTotals.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Account Type Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {accountTypeTotals.map(({ type, total, count }) => (
              <div
                key={type}
                className="p-4 border rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`p-2 rounded-lg ${getAccountTypeColor(type)} text-white`}
                  >
                    {getAccountIcon(type)}
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground">
                      {getAccountTypeLabel(type)}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {count} account{count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p
                    className={`text-xl font-bold ${
                      total >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {total >= 0 ? '+' : ''}${Math.abs(total).toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {((total / grandTotal) * 100).toFixed(1)}% of total
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Detailed Account List */}
          <div className="space-y-6">
            {Object.entries(groupedAccounts).map(([type, accounts]) => (
              <div key={type} className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    {getAccountIcon(type)}
                    {getAccountTypeLabel(type)}
                  </h3>
                  <div className="text-right">
                    <p
                      className={`text-lg font-semibold ${
                        accounts.reduce(
                          (sum, account) => sum + account.balance,
                          0
                        ) >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {accounts.reduce(
                        (sum, account) => sum + account.balance,
                        0
                      ) >= 0
                        ? '+'
                        : ''}
                      $
                      {Math.abs(
                        accounts.reduce(
                          (sum, account) => sum + account.balance,
                          0
                        )
                      ).toLocaleString()}
                    </p>
                    <span className="text-sm text-muted-foreground">
                      {accounts.length} account
                      {accounts.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {accounts.map(account => (
                    <div
                      key={account.id}
                      className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={`p-2 rounded-lg ${getAccountTypeColor(account.type)} text-white group-hover:scale-105 transition-transform`}
                          >
                            {getAccountIcon(account.type)}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h4 className="font-medium text-foreground truncate">
                              {account.name}
                            </h4>
                            <p className="text-sm text-muted-foreground truncate">
                              {account.entity || 'Unknown Entity'}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p
                          className={`text-xl font-semibold ${
                            account.balance >= 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {account.balance >= 0 ? '+' : ''}$
                          {Math.abs(account.balance).toLocaleString()}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>
                            Updated{' '}
                            {new Date(account.lastUpdated).toLocaleDateString()}
                          </span>
                          <span className="capitalize">{account.type}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
