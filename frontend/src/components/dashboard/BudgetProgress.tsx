import { BaseChart } from '@/components/dashboard/BaseChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
  remaining: number;
}

const mockCategories: BudgetCategory[] = [
  {
    name: 'Food & Dining',
    budget: 500,
    spent: 320,
    percentage: 64,
    color: '#3b82f6',
    remaining: 180,
  },
  {
    name: 'Transportation',
    budget: 300,
    spent: 180,
    percentage: 60,
    color: '#10b981',
    remaining: 120,
  },
  {
    name: 'Entertainment',
    budget: 200,
    spent: 150,
    percentage: 75,
    color: '#8b5cf6',
    remaining: 50,
  },
  {
    name: 'Shopping',
    budget: 400,
    spent: 520,
    percentage: 130,
    color: '#ef4444',
    remaining: -120,
  },
  {
    name: 'Utilities',
    budget: 250,
    spent: 220,
    percentage: 88,
    color: '#f59e0b',
    remaining: 30,
  },
  {
    name: 'Healthcare',
    budget: 150,
    spent: 80,
    percentage: 53,
    color: '#6366f1',
    remaining: 70,
  },
];

// Calculate total budget and spent
const totalBudget = mockCategories.reduce((sum, cat) => sum + cat.budget, 0);
const totalSpent = mockCategories.reduce((sum, cat) => sum + cat.spent, 0);
const totalRemaining = totalBudget - totalSpent;
const overallPercentage = Math.round((totalSpent / totalBudget) * 100);

const chartData = {
  series: [
    {
      name: 'Budget Usage',
      type: 'pie',
      radius: ['60%', '85%'],
      center: ['50%', '50%'],
      data: [
        {
          value: totalSpent,
          name: 'Spent',
          itemStyle: {
            color: overallPercentage > 100 ? '#ef4444' : '#3b82f6',
          },
        },
        {
          value: Math.max(0, totalRemaining),
          name: 'Remaining',
          itemStyle: {
            color: '#e5e7eb',
          },
        },
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
      label: {
        show: false,
      },
      labelLine: {
        show: false,
      },
    },
  ],
};

const chartOptions = {
  tooltip: {
    trigger: 'item',
    formatter: function (params: any) {
      const value = params.value;
      const percentage = Math.round((value / totalBudget) * 100);
      return `${params.name}: $${value.toLocaleString()} (${percentage}%)`;
    },
  },
  legend: {
    show: false,
  },
};

export function BudgetProgress() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Budget Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Donut Chart Section */}
          <div className="relative h-80 flex items-center justify-center">
            <div className="w-full">
              <BaseChart type="pie" data={chartData} options={chartOptions} />
            </div>
            {/* Center Text */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-foreground leading-none">
                  {overallPercentage}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Used</div>
                <div className="text-xs text-muted-foreground/70 mt-1">
                  ${totalSpent.toLocaleString()} / $
                  {totalBudget.toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Category Breakdown */}
          <CategoryBreakdown categories={mockCategories} />
        </div>
      </CardContent>
    </Card>
  );
}
