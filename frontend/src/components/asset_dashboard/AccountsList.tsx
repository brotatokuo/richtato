import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { formatSignedCurrency } from '@/lib/format';
import {
  AlertCircle,
  Building2,
  ChevronRight,
  CreditCard,
  Landmark,
  PiggyBank,
  Scale,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useEffect, useState } from 'react';

export interface AccountWithBalance extends Account {
  balance: number;
  lastUpdated: string;
}

const getAccountIcon = (type: string | undefined) => {
  switch ((type || '').toLowerCase()) {
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
      return <Landmark className="h-5 w-5" />;
  }
};

const getAccountTypeColor = (type: string | undefined) => {
  switch ((type || '').toLowerCase()) {
    case 'checking':
    case 'checking_account':
      return 'bg-blue-500';
    case 'savings':
    case 'savings_account':
      return 'bg-green-500';
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return 'bg-purple-500';
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

const getAccountTypeLabel = (type: string | undefined) => {
  switch ((type || '').toLowerCase()) {
    case 'checking':
    case 'checking_account':
      return 'Checking';
    case 'savings':
    case 'savings_account':
      return 'Savings';
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return 'Investment';
    case 'retirement':
    case '401k':
    case 'ira':
      return 'Retirement';
    case 'credit':
    case 'credit_card':
      return 'Credit Cards';
    case 'cash':
    case 'wallet':
      return 'Cash';
    default:
      return 'Other';
  }
};

// Sorting order for account types
const TYPE_ORDER: Record<string, number> = {
  checking: 1,
  checking_account: 1,
  savings: 2,
  savings_account: 2,
  investment: 3,
  investment_account: 3,
  brokerage: 3,
  retirement: 4,
  '401k': 4,
  ira: 4,
  credit: 5,
  credit_card: 5,
  cash: 6,
  wallet: 6,
};

export interface AccountGroup {
  type: string;
  typeDisplay: string;
  accounts: AccountWithBalance[];
  total: number;
}

interface AccountsListProps {
  selectedAccountId: number | null;
  selectedGroupType: string | null;
  onAccountSelect: (account: AccountWithBalance | null) => void;
  onGroupSelect: (group: AccountGroup | null) => void;
  onSetBalance?: (account: AccountWithBalance) => void;
  reloadKey?: string | number;
}

export function AccountsList({
  selectedAccountId,
  selectedGroupType,
  onAccountSelect,
  onGroupSelect,
  onSetBalance,
  reloadKey,
}: AccountsListProps) {
  const { preferences } = usePreferences();
  const [accounts, setAccounts] = useState<AccountWithBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAccounts = async () => {
      try {
        setLoading(true);
        setError(null);

        const accountsData = await transactionsApiService.getAccounts();

        const accountsWithBalance: AccountWithBalance[] = accountsData.map(
          a => {
            const accountWithExtras = a as Account & {
              balance?: number | string;
              date?: string;
            };
            return {
              ...a,
              balance:
                typeof accountWithExtras.balance === 'number'
                  ? accountWithExtras.balance
                  : Number(
                      String(accountWithExtras.balance || '0').replace(
                        /[^0-9.-]+/g,
                        ''
                      )
                    ),
              lastUpdated: String(accountWithExtras.date || ''),
            };
          }
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
  }, [reloadKey]);

  // Group accounts by type
  const groupedAccounts = accounts.reduce(
    (acc, account) => {
      const type = account.type || 'other';
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(account);
      return acc;
    },
    {} as Record<string, AccountWithBalance[]>
  );

  // Sort groups by type order
  const sortedGroups = Object.entries(groupedAccounts).sort(([a], [b]) => {
    const orderA = TYPE_ORDER[a.toLowerCase()] || 99;
    const orderB = TYPE_ORDER[b.toLowerCase()] || 99;
    return orderA - orderB;
  });

  if (loading) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Landmark className="h-5 w-5 text-primary" />
            Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
            <LoadingSpinner />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Landmark className="h-5 w-5 text-primary" />
            Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
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
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Landmark className="h-5 w-5 text-primary" />
            Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
            <div className="text-center text-muted-foreground">
              <Landmark className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No accounts found.</p>
              <p className="text-sm mt-1">Add accounts to track your assets.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-lg">
          <span className="flex items-center gap-2">
            <Landmark className="h-5 w-5 text-primary" />
            Accounts
          </span>
          <span className="text-sm font-normal text-muted-foreground">
            {accounts.length} account{accounts.length !== 1 ? 's' : ''}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {sortedGroups.map(([type, typeAccounts]) => {
          const typeTotal = typeAccounts.reduce(
            (sum, account) => sum + account.balance,
            0
          );
          const isGroupSelected = selectedGroupType === type;
          const group: AccountGroup = {
            type,
            typeDisplay: getAccountTypeLabel(type),
            accounts: typeAccounts,
            total: typeTotal,
          };

          return (
            <div key={type} className="space-y-2">
              {/* Type header - clickable */}
              <button
                onClick={() => {
                  // Clear individual account selection when selecting a group
                  onAccountSelect(null);
                  onGroupSelect(isGroupSelected ? null : group);
                }}
                className={`w-full flex items-center justify-between px-2 py-1.5 rounded-md transition-all ${
                  isGroupSelected
                    ? 'bg-primary/10 ring-1 ring-primary'
                    : 'hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <div
                    className={`w-2 h-2 rounded-full ${getAccountTypeColor(type)}`}
                  />
                  <span className={isGroupSelected ? 'text-primary' : ''}>
                    {getAccountTypeLabel(type)}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({typeAccounts.length})
                  </span>
                </div>
                <span
                  className={`text-sm font-semibold ${
                    typeTotal >= 0 ? 'text-green-600' : 'text-red-500'
                  }`}
                >
                  {formatSignedCurrency(typeTotal, preferences.currency, true)}
                </span>
              </button>

              {/* Account items - indented under group */}
              <div className="space-y-1">
                {typeAccounts.map(account => {
                  const isSelected = selectedAccountId === account.id;

                  return (
                    <button
                      key={account.id}
                      onClick={() => {
                        // Clear group selection when selecting an individual account
                        onGroupSelect(null);
                        onAccountSelect(isSelected ? null : account);
                      }}
                      className={`w-full p-3 rounded-lg border transition-all text-left flex items-center justify-between group ${
                        isSelected
                          ? 'bg-primary/10 border-primary ring-1 ring-primary'
                          : 'bg-card/50 border-border/50 hover:bg-muted/50 hover:border-border'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div
                          className={`p-2 rounded-lg ${getAccountTypeColor(account.type)} text-white shrink-0`}
                        >
                          {getAccountIcon(account.type)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-foreground truncate">
                            {account.name}
                          </p>
                          {account.lastUpdated && (
                            <p className="text-xs text-muted-foreground">
                              {new Date(account.lastUpdated + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0 ml-2">
                        <span
                          className={`font-semibold ${
                            account.balance >= 0
                              ? 'text-green-600'
                              : 'text-red-500'
                          }`}
                        >
                          {formatSignedCurrency(
                            account.balance,
                            preferences.currency,
                            true
                          )}
                        </span>
                        {onSetBalance && (
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              onSetBalance(account);
                            }}
                            className="p-1 rounded-md text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-primary/10 hover:text-primary transition-all"
                            title="Set balance"
                          >
                            <Scale className="h-4 w-4" />
                          </button>
                        )}
                        <ChevronRight
                          className={`h-4 w-4 text-muted-foreground transition-transform ${
                            isSelected
                              ? 'rotate-90 text-primary'
                              : 'group-hover:translate-x-0.5'
                          }`}
                        />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
