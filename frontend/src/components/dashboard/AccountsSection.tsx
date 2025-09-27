import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, PiggyBank, TrendingUp } from 'lucide-react';

interface Account {
  id: string;
  name: string;
  type: string;
  balance: number;
  entity: string;
  lastUpdated: string;
}

const mockAccounts: Account[] = [
  {
    id: '1',
    name: 'Primary Checking',
    type: 'checking',
    balance: 5420.5,
    entity: 'Chase Bank',
    lastUpdated: '2024-01-15',
  },
  {
    id: '2',
    name: 'High Yield Savings',
    type: 'savings',
    balance: 12500.0,
    entity: 'Ally Bank',
    lastUpdated: '2024-01-14',
  },
  {
    id: '3',
    name: 'Investment Portfolio',
    type: 'investment',
    balance: 45000.0,
    entity: 'Vanguard',
    lastUpdated: '2024-01-15',
  },
  {
    id: '4',
    name: '401(k) Retirement',
    type: 'retirement',
    balance: 85000.0,
    entity: 'Fidelity',
    lastUpdated: '2024-01-15',
  },
];

const getAccountIcon = (type: string) => {
  switch (type) {
    case 'checking':
      return <Building2 className="h-5 w-5" />;
    case 'savings':
      return <PiggyBank className="h-5 w-5" />;
    case 'investment':
      return <TrendingUp className="h-5 w-5" />;
    case 'retirement':
      return <TrendingUp className="h-5 w-5" />;
    default:
      return <Building2 className="h-5 w-5" />;
  }
};

const getAccountTypeColor = (type: string) => {
  switch (type) {
    case 'checking':
      return 'bg-blue-500';
    case 'savings':
      return 'bg-green-500';
    case 'investment':
      return 'bg-purple-500';
    case 'retirement':
      return 'bg-orange-500';
    default:
      return 'bg-gray-500';
  }
};

export function AccountsSection() {
  const groupedAccounts = mockAccounts.reduce(
    (acc, account) => {
      if (!acc[account.type]) {
        acc[account.type] = [];
      }
      acc[account.type].push(account);
      return acc;
    },
    {} as Record<string, Account[]>
  );

  const accountTypeLabels = {
    checking: 'Checking',
    savings: 'Savings',
    investment: 'Investments',
    retirement: 'Retirement',
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Accounts</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {Object.entries(groupedAccounts).map(([type, accounts]) => (
            <div key={type} className="space-y-3">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                {getAccountIcon(type)}
                {accountTypeLabels[type as keyof typeof accountTypeLabels]}
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {accounts.map(account => (
                  <div
                    key={account.id}
                    className="p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`p-2 rounded-lg ${getAccountTypeColor(account.type)} text-white`}
                        >
                          {getAccountIcon(account.type)}
                        </div>
                        <div>
                          <h4 className="font-medium text-foreground">
                            {account.name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {account.entity}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <p
                        className={`text-lg font-semibold ${
                          account.balance >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {account.balance >= 0 ? '+' : ''}$
                        {Math.abs(account.balance).toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Updated{' '}
                        {new Date(account.lastUpdated).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
