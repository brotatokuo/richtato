import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
}

const mockCategories: BudgetCategory[] = [
  {
    name: 'Food & Dining',
    budget: 500,
    spent: 320,
    percentage: 64,
    color: 'bg-blue-500',
  },
  {
    name: 'Transportation',
    budget: 300,
    spent: 180,
    percentage: 60,
    color: 'bg-green-500',
  },
  {
    name: 'Entertainment',
    budget: 200,
    spent: 150,
    percentage: 75,
    color: 'bg-purple-500',
  },
  {
    name: 'Shopping',
    budget: 400,
    spent: 520,
    percentage: 130,
    color: 'bg-red-500',
  },
  {
    name: 'Utilities',
    budget: 250,
    spent: 220,
    percentage: 88,
    color: 'bg-yellow-500',
  },
  {
    name: 'Healthcare',
    budget: 150,
    spent: 80,
    percentage: 53,
    color: 'bg-indigo-500',
  },
];

export function BudgetProgress() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Budget Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {mockCategories.map(category => (
          <div key={category.name} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{category.name}</span>
              <span className="text-sm text-muted-foreground">
                ${category.spent.toLocaleString()} / $
                {category.budget.toLocaleString()}
              </span>
            </div>
            <div className="space-y-1">
              <Progress
                value={Math.min(category.percentage, 100)}
                className="h-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{category.percentage}% used</span>
                {category.percentage > 100 && (
                  <span className="text-red-500 font-medium">
                    ${(category.spent - category.budget).toLocaleString()} over
                    budget
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
