import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

// Function to get computed CSS values
const getCSSValue = (property: string) => {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
};

interface ExpenseCategory {
  name: string;
  value: number;
  percentage: number;
  color: string;
}

export function ExpenseBreakdown() {
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [themeKey, setThemeKey] = useState(0);
  const [expenseCategories, setExpenseCategories] = useState<ExpenseCategory[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch expense data from API
  const fetchExpenseData = async () => {
    try {
      setLoading(true);
      setError(null);

      const expenseTransactions =
        await transactionsApiService.getExpenseTransactions();

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

      // Calculate total expenses
      const totalExpenses = Object.values(expensesByCategory).reduce(
        (sum, amount) => sum + amount,
        0
      );

      // Get chart colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');

      // Convert to ExpenseCategory format
      const categories = Object.entries(expensesByCategory).map(
        ([name, value], index) => ({
          name,
          value,
          percentage:
            totalExpenses > 0 ? Math.round((value / totalExpenses) * 100) : 0,
          color: `hsl(${[chart1, chart2, chart3, chart4, chart5, chart6][index % 6]})`,
        })
      );

      setExpenseCategories(categories);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load expense data'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenseData();
  }, []);

  useEffect(() => {
    if (expenseCategories.length === 0) return;

    // Get actual CSS values
    const cardColor = getCSSValue('--card');
    const cardForegroundColor = getCSSValue('--card-foreground');
    const borderColor = getCSSValue('--border');

    const data = {
      series: [
        {
          name: 'Expense Breakdown',
          type: 'pie',
          radius: ['60%', '85%'],
          center: ['50%', '50%'],
          data: expenseCategories.map(expense => ({
            value: expense.value,
            name: expense.name,
            itemStyle: {
              color: expense.color,
            },
          })),
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

    const options = {
      tooltip: {
        trigger: 'item',
        backgroundColor: `hsl(${cardColor})`,
        borderColor: `hsl(${borderColor})`,
        textStyle: {
          color: `hsl(${cardForegroundColor})`,
        },
        formatter: function (params: any) {
          return `${params.name}: $${params.value.toLocaleString()}`;
        },
      },
      legend: {
        show: false,
      },
    };

    setChartData(data);
    setChartOptions(options);
  }, [expenseCategories, themeKey]);

  // Listen for theme changes
  useEffect(() => {
    const handleThemeChange = () => {
      setThemeKey(prev => prev + 1);
    };

    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'class'
        ) {
          handleThemeChange();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Expense Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span className="text-muted-foreground">Loading...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Expense Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchExpenseData}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mx-auto"
              >
                <RefreshCw className="h-4 w-4" />
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
          <CardTitle>Expense Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">No data available</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expense Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Donut Chart Section */}
          <div className="relative h-80 flex items-center justify-center">
            <div className="w-full">
              <BaseChart
                key={themeKey}
                type="pie"
                data={chartData}
                options={chartOptions}
              />
            </div>
            {/* Center Text */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-foreground leading-none">
                  {expenseCategories.length}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  Categories
                </div>
                <div className="text-xs text-muted-foreground/70 mt-1">
                  Total Expenses
                </div>
              </div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="space-y-3">
            {expenseCategories.map((expense, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/30"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{
                      backgroundColor: expense.color,
                    }}
                  />
                  <span className="text-foreground font-medium">
                    {expense.name}
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-foreground">
                    {expense.percentage}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ${expense.value.toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
