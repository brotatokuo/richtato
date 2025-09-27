import { BaseChart } from '@/components/dashboard/BaseChart';
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
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '3%',
    containLabel: true,
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
          <div className="relative">
            <div className="h-64">
              <BaseChart type="pie" data={chartData} options={chartOptions} />
            </div>
            {/* Center Text */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">
                  {overallPercentage}%
                </div>
                <div className="text-sm text-gray-500">Used</div>
                <div className="text-xs text-gray-400 mt-1">
                  ${totalSpent.toLocaleString()} / $
                  {totalBudget.toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="space-y-3">
            <div className="text-sm font-medium text-gray-700 mb-4">
              Category Breakdown
            </div>
            {mockCategories.map(category => (
              <div
                key={category.name}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="text-sm font-medium text-gray-900">
                    {category.name}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-900">
                    ${category.spent.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">
                    of ${category.budget.toLocaleString()}
                  </div>
                  <div
                    className={`text-xs font-medium ${
                      category.percentage > 100
                        ? 'text-red-600'
                        : category.percentage > 80
                          ? 'text-yellow-600'
                          : 'text-green-600'
                    }`}
                  >
                    {category.percentage}%
                    {category.remaining < 0 && (
                      <span className="ml-1">
                        (Over by $
                        {Math.abs(category.remaining).toLocaleString()})
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${totalBudget.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Total Budget</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${totalSpent.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Total Spent</div>
          </div>
          <div className="text-center">
            <div
              className={`text-2xl font-bold ${
                totalRemaining >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              ${Math.abs(totalRemaining).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">
              {totalRemaining >= 0 ? 'Remaining' : 'Over Budget'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
