import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

const mockExpenses: ExpenseCategory[] = [
  {
    name: 'Food & Dining',
    value: 28,
    percentage: 28,
    color: '#3b82f6',
  },
  {
    name: 'Shopping',
    value: 22,
    percentage: 22,
    color: '#10b981',
  },
  {
    name: 'Transportation',
    value: 15,
    percentage: 15,
    color: '#8b5cf6',
  },
  {
    name: 'Entertainment',
    value: 9,
    percentage: 9,
    color: '#f59e0b',
  },
  {
    name: 'Utilities',
    value: 8,
    percentage: 8,
    color: '#ef4444',
  },
  {
    name: 'Healthcare',
    value: 6,
    percentage: 6,
    color: '#6366f1',
  },
];

export function ExpenseBreakdown() {
  const [chartData, setChartData] = useState(null);
  const [chartOptions, setChartOptions] = useState(null);
  const [themeKey, setThemeKey] = useState(0);

  useEffect(() => {
    // Get actual CSS values
    const foregroundColor = getCSSValue('--foreground');
    const cardColor = getCSSValue('--card');
    const cardForegroundColor = getCSSValue('--card-foreground');
    const borderColor = getCSSValue('--border');

    // Get chart colors
    const chart1 = getCSSValue('--chart-1');
    const chart2 = getCSSValue('--chart-2');
    const chart3 = getCSSValue('--chart-3');
    const chart4 = getCSSValue('--chart-4');
    const chart5 = getCSSValue('--chart-5');
    const chart6 = getCSSValue('--chart-6');

    const data = {
      series: [
        {
          name: 'Expense Breakdown',
          type: 'pie',
          radius: ['60%', '85%'],
          center: ['50%', '50%'],
          data: mockExpenses.map((expense, index) => ({
            value: expense.value,
            name: expense.name,
            itemStyle: {
              color: `hsl(${[chart1, chart2, chart3, chart4, chart5, chart6][index]})`,
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
          return `${params.name}: ${params.value}%`;
        },
      },
      legend: {
        show: false,
      },
    };

    setChartData(data);
    setChartOptions(options);
  }, [themeKey]);

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

  if (!chartData || !chartOptions) {
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
                  {mockExpenses.length}
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
            {mockExpenses.map((expense, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/30"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{
                      backgroundColor: `hsl(${getCSSValue(`--chart-${(index % 6) + 1}`)})`,
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
                    ${expense.value * 10}
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
