import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBudgetDateRange } from '@/contexts/BudgetDateRangeContext';
import { dashboardApiService } from '@/lib/api/dashboard';
import { AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PieWithDetailedLegend } from './PieWithDetailedLegend';

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
  const { startDate, endDate } = useBudgetDateRange();
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
      const data = await dashboardApiService.getExpenseCategoriesData({
        startDate,
        endDate,
      });
      const labels = data.labels || [];
      const values = (data.datasets?.[0]?.data as number[]) || [];
      const expensesByCategory = labels.map((name, idx) => ({
        name,
        value: values[idx] || 0,
      }));
      const totalExpenses = values.reduce((sum, v) => sum + (v || 0), 0);

      // Get chart colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');

      // Convert to ExpenseCategory format
      const categories = expensesByCategory.map((entry, index) => ({
        name: entry.name,
        value: entry.value,
        percentage:
          totalExpenses > 0
            ? Math.round(((entry.value || 0) / totalExpenses) * 100)
            : 0,
        color: `hsl(${[chart1, chart2, chart3, chart4, chart5, chart6][index % 6]})`,
      }));

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
  }, [startDate, endDate]);

  useEffect(() => {
    if (expenseCategories.length === 0) return;

    const data = {
      series: [
        {
          name: 'Expense Breakdown',
          type: 'pie',
          radius: ['60%', '85%'],
          center: ['50%', '50%'],
          hoverAnimation: false,
          selectedMode: false,
          data: expenseCategories.map(expense => ({
            value: expense.value,
            name: expense.name,
            itemStyle: {
              color: expense.color,
            },
          })),
          emphasis: { disabled: true },
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
        showDelay: 0,
        hideDelay: 0,
        confine: true,
        transitionDuration: 0.05,
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
          <CardTitle>Expense Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600">{error}</p>
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
    <PieWithDetailedLegend
      title="Expense Breakdown"
      chartData={chartData}
      chartOptions={chartOptions}
      centerPrimary={expenseCategories.length}
      centerSecondaryLabel="Categories"
      centerTertiaryLabel="Total Expenses"
      chartKey={themeKey}
      legend={
        <div className="h-80 overflow-y-auto">
          <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2">
            {expenseCategories.map((expense, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 rounded-md bg-muted/20"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: expense.color,
                    }}
                  />
                  <span className="text-sm text-foreground font-medium">
                    {expense.name}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-foreground">
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
      }
    />
  );
}
