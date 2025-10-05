import { BaseChart } from '@/components/dashboard/BaseChart';
import { CategoryBreakdown } from '@/components/dashboard/CategoryBreakdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';

interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
  remaining: number;
}

// Function to get computed CSS values
const getCSSValue = (property: string) => {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
};

export function BudgetProgress() {
  const [budgetCategories, setBudgetCategories] = useState<BudgetCategory[]>(
    []
  );
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch budget data from API
  const fetchBudgetData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [budgets, expenseTransactions] = await Promise.all([
        transactionsApiService.getBudgets(),
        transactionsApiService.getExpenseTransactions(),
      ]);

      // Get chart colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');

      // Group expenses by category
      const expensesByCategory = expenseTransactions.reduce(
        (acc, transaction) => {
          const category = transaction.Category || 'Uncategorized';
          if (!acc[category]) {
            acc[category] = 0;
          }
          acc[category] += transaction.amount;
          return acc;
        },
        {} as Record<string, number>
      );

      // Create budget categories by matching budgets with expenses
      const categories: BudgetCategory[] = budgets.map((budget, index) => {
        const spent = expensesByCategory[budget.category] || 0;
        const percentage =
          budget.amount > 0 ? Math.round((spent / budget.amount) * 100) : 0;
        const remaining = budget.amount - spent;

        return {
          name: budget.category,
          budget: budget.amount,
          spent,
          percentage,
          color: `hsl(${[chart1, chart2, chart3, chart4, chart5, chart6][index % 6]})`,
          remaining,
        };
      });

      setBudgetCategories(categories);

      // Calculate totals
      const totalBudget = categories.reduce((sum, cat) => sum + cat.budget, 0);
      const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0);
      const totalRemaining = totalBudget - totalSpent;
      const overallPercentage =
        totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

      // Create chart data
      const chartDataObj = {
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

      const chartOptionsObj = {
        tooltip: {
          trigger: 'item',
          formatter: function (params: any) {
            const value = params.value;
            const percentage =
              totalBudget > 0 ? Math.round((value / totalBudget) * 100) : 0;
            return `${params.name}: $${value.toLocaleString()} (${percentage}%)`;
          },
        },
        legend: {
          show: false,
        },
      };

      setChartData(chartDataObj);
      setChartOptions(chartOptionsObj);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load budget data'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgetData();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">Loading...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchBudgetData}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 mx-auto"
              >
                Retry
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!chartData || !chartOptions) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">
              No budget data available
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate totals for display
  const totalBudget = budgetCategories.reduce(
    (sum, cat) => sum + cat.budget,
    0
  );
  const totalSpent = budgetCategories.reduce((sum, cat) => sum + cat.spent, 0);
  const overallPercentage =
    totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

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
          <CategoryBreakdown categories={budgetCategories} />
        </div>
      </CardContent>
    </Card>
  );
}
