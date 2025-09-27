import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Income',
      data: [3500, 3500, 3600, 3500, 3700, 3800],
      backgroundColor: 'rgba(34, 197, 94, 0.2)',
      borderColor: 'rgba(34, 197, 94, 1)',
      borderWidth: 2,
    },
    {
      label: 'Expenses',
      data: [2800, 3200, 2900, 3100, 3000, 3200],
      backgroundColor: 'rgba(239, 68, 68, 0.2)',
      borderColor: 'rgba(239, 68, 68, 1)',
      borderWidth: 2,
    },
  ],
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: function (value: any) {
          return '$' + value.toLocaleString();
        },
      },
    },
  },
};

export function IncomeExpenseChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Income vs Expenses</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <BaseChart type="bar" data={mockData} options={chartOptions} />
        </div>
      </CardContent>
    </Card>
  );
}
