import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  labels: [
    'Food & Dining',
    'Shopping',
    'Transportation',
    'Entertainment',
    'Utilities',
    'Healthcare',
  ],
  datasets: [
    {
      data: [28, 22, 15, 9, 8, 6],
      backgroundColor: [
        'rgba(59, 130, 246, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(139, 92, 246, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(236, 72, 153, 0.8)',
      ],
      borderColor: [
        'rgba(59, 130, 246, 1)',
        'rgba(16, 185, 129, 1)',
        'rgba(245, 158, 11, 1)',
        'rgba(139, 92, 246, 1)',
        'rgba(239, 68, 68, 1)',
        'rgba(236, 72, 153, 1)',
      ],
      borderWidth: 2,
    },
  ],
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
    tooltip: {
      callbacks: {
        label: function (context: any) {
          const label = context.label || '';
          const value = context.parsed;
          return `${label}: ${value}%`;
        },
      },
    },
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
