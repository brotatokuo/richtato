import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Savings',
      data: [700, 300, 700, 400, 700, 600],
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 2,
      fill: true,
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

export function SavingsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Savings Accumulation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <BaseChart type="line" data={mockData} options={chartOptions} />
        </div>
      </CardContent>
    </Card>
  );
}
