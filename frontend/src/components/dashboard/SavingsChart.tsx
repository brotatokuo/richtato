import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  series: [
    {
      name: 'Savings',
      type: 'line',
      data: [700, 300, 700, 400, 700, 600],
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.1)' },
          ],
        },
      },
      lineStyle: {
        color: '#3b82f6',
        width: 2,
      },
      itemStyle: {
        color: '#3b82f6',
      },
    },
  ],
};

const chartOptions = {
  title: {
    text: 'Savings Accumulation',
    left: 'center',
  },
  tooltip: {
    trigger: 'axis',
    formatter: function (params: any) {
      const param = params[0];
      return (
        param.name +
        '<br/>' +
        param.seriesName +
        ': $' +
        param.value.toLocaleString()
      );
    },
  },
  legend: {
    data: ['Savings'],
    top: 'bottom',
  },
  xAxis: {
    type: 'category',
    data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: function (value: number) {
        return '$' + value.toLocaleString();
      },
    },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '10%',
    containLabel: true,
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
