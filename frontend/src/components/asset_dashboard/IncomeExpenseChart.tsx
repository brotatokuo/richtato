import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CashFlowData,
  assetDashboardApiService,
} from '@/lib/api/asset-dashboard';
import { useEffect, useMemo, useState } from 'react';

export function IncomeExpenseChart() {
  const [period, setPeriod] = useState<'3m' | '6m' | '12m' | 'ytd'>('6m');
  const [remoteData, setRemoteData] = useState<CashFlowData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const computeRange = (p: '3m' | '6m' | '12m' | 'ytd') => {
    const end = new Date();
    let start: Date;
    if (p === 'ytd') {
      start = new Date(end.getFullYear(), 0, 1);
    } else {
      const months = p === '3m' ? 3 : p === '6m' ? 6 : 12;
      start = new Date(end.getFullYear(), end.getMonth() - (months - 1), 1);
    }
    const toIso = (d: Date) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
        d.getDate()
      ).padStart(2, '0')}`;
    return { startDate: toIso(start), endDate: toIso(end) };
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const { startDate, endDate } = computeRange(period);
        const resp = await assetDashboardApiService.getIncomeExpensesData({
          startDate,
          endDate,
        });
        setRemoteData(resp);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load chart data');
        setRemoteData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [period]);

  const sourceData = remoteData;

  // Convert API data to chart format
  const getChartData = () => {
    if (!sourceData) return null;

    const chartData = {
      series: sourceData.datasets.map(dataset => ({
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
        data: sourceData.labels,
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

  const chartConfig = useMemo(getChartData, [sourceData]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Income vs Expenses</CardTitle>
          <div className="w-40">
            <Select value={period} onValueChange={v => setPeriod(v as any)}>
              <SelectTrigger aria-label="Select period">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3m">Last 3 months</SelectItem>
                <SelectItem value="6m">Last 6 months</SelectItem>
                <SelectItem value="12m">Last 12 months</SelectItem>
                <SelectItem value="ytd">Year to date</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-muted-foreground">Loading chart data...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-red-500">{error}</div>
          </div>
        ) : sourceData && chartConfig ? (
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
