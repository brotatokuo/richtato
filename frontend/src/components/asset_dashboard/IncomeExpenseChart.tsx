import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CashFlowData } from '@/lib/api/dashboard';

interface IncomeExpenseChartProps {
  data: CashFlowData | null;
}

export function IncomeExpenseChart({ data }: IncomeExpenseChartProps) {
  // Convert API data to chart format
  const getChartData = () => {
    if (!data) return null;

    const chartData = {
      series: data.datasets.map(dataset => ({
        name: dataset.label,
        type: 'bar',
        data: dataset.data,
        itemStyle: {
          color:
            dataset.backgroundColor ||
            (dataset.label === 'Income' ? '#22c55e' : '#ef4444'),
        },
      })),
    };

    const chartOptions = {
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
      xAxis: {
        type: 'category',
        data: data.labels,
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

    return { data: chartData, options: chartOptions };
  };

  const chartConfig = getChartData();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income vs Expenses</CardTitle>
      </CardHeader>
      <CardContent>
        {data && chartConfig ? (
          <BaseChart
            type="bar"
            data={chartConfig.data}
            options={chartConfig.options}
          />
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-muted-foreground">Loading chart data...</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
