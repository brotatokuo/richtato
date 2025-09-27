import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const mockData = {
  series: [
    {
      name: 'Income',
      type: 'bar',
      data: [3500, 3500, 3600, 3500, 3700, 3800],
      itemStyle: {
        color: '#22c55e',
      },
    },
    {
      name: 'Expenses',
      type: 'bar',
      data: [2800, 3200, 2900, 3100, 3000, 3200],
      itemStyle: {
        color: '#ef4444',
      },
    },
  ],
};

const chartOptions = {
  title: {
    text: 'Income vs Expenses',
    left: 'center',
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow',
    },
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
    data: ['Income', 'Expenses'],
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
