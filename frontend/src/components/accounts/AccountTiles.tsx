import { Card, CardContent } from '@/components/ui/card';
import { formatSignedCurrency } from '@/lib/format';
import { Account } from '@/lib/api/transactions';
import {
  Building2,
  CreditCard,
  PiggyBank,
  TrendingUp,
  Wallet,
  AlertCircle,
} from 'lucide-react';

interface AccountTilesProps {
  accounts: Account[];
  selectedAccountId: number | null;
  onAccountSelect: (accountId: number | null) => void;
  currency: string;
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
      return 'bg-primary text-primary-foreground';
    case 'savings':
    case 'savings_account':
      return 'bg-green-500 text-white';
    case 'investment':
    case 'investment_account':
    case 'brokerage':
      return 'bg-secondary text-secondary-foreground';
    case 'retirement':
    case '401k':
    case 'ira':
      return 'bg-orange-500 text-white';
    case 'credit':
    case 'credit_card':
      return 'bg-red-500 text-white';
    case 'cash':
    case 'wallet':
      return 'bg-yellow-500 text-white';
    default:
      return 'bg-gray-500 text-white';
  }
};

export function AccountTiles({
  accounts,
  selectedAccountId,
  onAccountSelect,
  currency,
}: AccountTilesProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {/* "All Accounts" tile */}
      <Card
        className={`cursor-pointer transition-all hover:shadow-md ${
          selectedAccountId === null
            ? 'ring-2 ring-secondary shadow-lg'
            : 'hover:ring-1 hover:ring-secondary/50'
        }`}
        onClick={() => onAccountSelect(null)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-primary to-secondary text-white">
                <Wallet className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">All Accounts</h3>
                <p className="text-xs text-muted-foreground">View all</p>
              </div>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-foreground">
              {formatSignedCurrency(
                accounts.reduce((sum, acc) => {
                  const balance =
                    typeof acc.balance === 'number'
                      ? acc.balance
                      : Number(
                          String(acc.balance || '0').replace(/[^0-9.-]+/g, '')
                        );
                  return sum + balance;
                }, 0),
                currency,
                true
              )}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {accounts.length} account{accounts.length !== 1 ? 's' : ''}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Individual account tiles */}
      {accounts.map(account => {
        const balance =
          typeof account.balance === 'number'
            ? account.balance
            : Number(String(account.balance || '0').replace(/[^0-9.-]+/g, ''));
        const isSelected = selectedAccountId === account.id;

        return (
          <Card
            key={account.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              isSelected
                ? 'ring-2 ring-secondary shadow-lg'
                : 'hover:ring-1 hover:ring-secondary/50'
            }`}
            onClick={() => onAccountSelect(account.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${getAccountTypeColor(account.type)}`}
                  >
                    {getAccountIcon(account.type)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-foreground truncate">
                      {account.name}
                    </h3>
                    <p className="text-xs text-muted-foreground truncate">
                      {account.entity || 'No entity'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-2">
                <p
                  className={`text-2xl font-bold ${
                    balance >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatSignedCurrency(balance, currency, true)}
                </p>
                <p className="text-xs text-muted-foreground capitalize mt-1">
                  {account.type.replace(/_/g, ' ')}
                </p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
