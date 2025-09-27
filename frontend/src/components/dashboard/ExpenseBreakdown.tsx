import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  series: [
    {
      name: 'Expense Breakdown',
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 28, name: 'Food & Dining', itemStyle: { color: '#3b82f6' } },
        { value: 22, name: 'Shopping', itemStyle: { color: '#10b981' } },
        { value: 15, name: 'Transportation', itemStyle: { color: '#f59e0b' } },
        { value: 9, name: 'Entertainment', itemStyle: { color: '#8b5cf6' } },
        { value: 8, name: 'Utilities', itemStyle: { color: '#ef4444' } },
        { value: 6, name: 'Healthcare', itemStyle: { color: '#ec4899' } },
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    },
  ],
};

const chartOptions = {
  title: {
    text: 'Expense Breakdown',
    left: 'center',
  },
  tooltip: {
    trigger: 'item',
    formatter: function (params: any) {
      return params.name + ': ' + params.value + '%';
    },
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    data: [
      'Food & Dining',
      'Shopping',
      'Transportation',
      'Entertainment',
      'Utilities',
      'Healthcare',
    ],
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true,
  },
};

export function ExpenseBreakdown() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Expense Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <BaseChart type="doughnut" data={mockData} options={chartOptions} />
        </div>
      </CardContent>
    </Card>
  );
}
