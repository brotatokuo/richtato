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

export function ExpenseBreakdown() {
  const [chartData, setChartData] = useState(null);
  const [chartOptions, setChartOptions] = useState(null);

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
          radius: ['40%', '70%'],
          data: [
            {
              value: 28,
              name: 'Food & Dining',
              itemStyle: { color: `hsl(${chart1})` },
            },
            {
              value: 22,
              name: 'Shopping',
              itemStyle: { color: `hsl(${chart2})` },
            },
            {
              value: 15,
              name: 'Transportation',
              itemStyle: { color: `hsl(${chart3})` },
            },
            {
              value: 9,
              name: 'Entertainment',
              itemStyle: { color: `hsl(${chart4})` },
            },
            {
              value: 8,
              name: 'Utilities',
              itemStyle: { color: `hsl(${chart5})` },
            },
            {
              value: 6,
              name: 'Healthcare',
              itemStyle: { color: `hsl(${chart6})` },
            },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: `hsl(${foregroundColor} / 0.2)`,
            },
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
          return params.name + ': ' + params.value + '%';
        },
      },
    };

    setChartData(data);
    setChartOptions(options);
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
        <div className="w-full overflow-hidden">
          <BaseChart type="doughnut" data={chartData} options={chartOptions} />
        </div>
      </CardContent>
    </Card>
  );
}
