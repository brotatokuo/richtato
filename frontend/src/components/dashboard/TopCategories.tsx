import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Category {
  name: string;
  amount: number;
  transactions: number;
  percentage: number;
}

const mockCategories: Category[] = [
  { name: 'Food & Dining', amount: 1250, transactions: 45, percentage: 28 },
  { name: 'Shopping', amount: 980, transactions: 23, percentage: 22 },
  { name: 'Transportation', amount: 650, transactions: 18, percentage: 15 },
  { name: 'Entertainment', amount: 420, transactions: 12, percentage: 9 },
  { name: 'Utilities', amount: 380, transactions: 8, percentage: 8 },
  { name: 'Healthcare', amount: 250, transactions: 5, percentage: 6 },
  { name: 'Other', amount: 180, transactions: 7, percentage: 4 },
];

export function TopCategories() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Spending Categories</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockCategories.map((category, index) => (
            <div key={category.name} className="flex items-center space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-foreground truncate">
                    {category.name}
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    ${category.amount.toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs text-muted-foreground">
                    {category.transactions} transactions
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {category.percentage}%
                  </p>
                </div>
                <div className="mt-2 w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full"
                    style={{ width: `${category.percentage}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
