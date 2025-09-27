import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  series: [
    {
      name: 'Income',
      type: 'line',
      data: [3500, 3500, 3600, 3500, 3700, 3800],
      smooth: true,
      lineStyle: {
        color: '#22c55e',
        width: 2,
      },
      itemStyle: {
        color: '#22c55e',
      },
    },
    {
      name: 'Expenses',
      type: 'line',
      data: [2800, 3200, 2900, 3100, 3000, 3200],
      smooth: true,
      lineStyle: {
        color: '#ef4444',
        width: 2,
      },
      itemStyle: {
        color: '#ef4444',
      },
    },
    {
      name: 'Savings',
      type: 'line',
      data: [700, 300, 700, 400, 700, 600],
      smooth: true,
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
    text: 'Cash Flow',
    left: 'center',
  },
  tooltip: {
    trigger: 'axis',
    formatter: function (params: any) {
      let result = params[0].name + '<br/>';
      params.forEach((param: any) => {
        result +=
          param.seriesName + ': $' + param.value.toLocaleString() + '<br/>';
      });
      return result;
    },
  },
  legend: {
    data: ['Income', 'Expenses', 'Savings'],
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

export function CashFlowChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cash Flow</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <BaseChart type="line" data={mockData} options={chartOptions} />
        </div>
      </CardContent>
    </Card>
  );
}
