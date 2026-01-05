import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { formatCurrency } from '@/lib/format';
import type { MonthlyBudgetData } from '@/lib/api/budget-dashboard';
import { BarChart3, LineChart, Percent } from 'lucide-react';
import { useMemo, useState } from 'react';

interface BudgetTrendsChartProps {
  monthlyData: MonthlyBudgetData[];
  loading?: boolean;
}

type ChartView = 'line' | 'bar' | 'percentage';

export function BudgetTrendsChart({
  monthlyData,
  loading,
}: BudgetTrendsChartProps) {
  const { preferences } = usePreferences();
  const [activeView, setActiveView] = useState<ChartView>('bar');

  const labels = useMemo(
    () => monthlyData.map((m) => m.label),
    [monthlyData]
  );

  const lineChartOptions = useMemo(() => {
    const currency = preferences.currency;
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params: Array<{ name?: string; color?: string; seriesName?: string; value?: number | number[] }>) {
          const lines = (params || []).map((p) => {
            const value = Array.isArray(p.value) ? p.value[1] : p.value;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${p.color};"></span>${p.seriesName}: ${formatCurrency(value as number, currency)}`;
          });
          const name = params?.[0]?.name ?? '';
          return [name, ...lines].join('<br/>');
        },
      },
      legend: {
        show: true,
        bottom: 0,
        textStyle: { color: '#9ca3af' },
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: {
          color: '#9ca3af',
          fontSize: 11,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#9ca3af',
          formatter: function (value: number) {
            return formatCurrency(value, currency);
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
  }, [labels, preferences.currency]);

  const lineChartData = useMemo(() => {
    return {
      series: [
        {
          name: 'Spent',
          type: 'line',
          data: monthlyData.map((m) => m.total_spent),
          smooth: true,
          lineStyle: { color: '#ef4444', width: 2 },
          itemStyle: { color: '#ef4444' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
                { offset: 1, color: 'rgba(239, 68, 68, 0.05)' },
              ],
            },
          },
        },
        {
          name: 'Budget',
          type: 'line',
          data: monthlyData.map((m) => m.total_budget),
          smooth: true,
          lineStyle: { color: '#3b82f6', width: 2, type: 'dashed' },
          itemStyle: { color: '#3b82f6' },
        },
      ],
    };
  }, [monthlyData]);

  const barChartOptions = useMemo(() => {
    const currency = preferences.currency;
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function (params: Array<{ name?: string; color?: string; seriesName?: string; value?: number | number[] }>) {
          const lines = (params || []).map((p) => {
            const value = Array.isArray(p.value) ? p.value[1] : p.value;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${p.color};"></span>${p.seriesName}: ${formatCurrency(value as number, currency)}`;
          });
          const name = params?.[0]?.name ?? '';
          return [name, ...lines].join('<br/>');
        },
      },
      legend: {
        show: true,
        bottom: 0,
        textStyle: { color: '#9ca3af' },
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: {
          color: '#9ca3af',
          fontSize: 11,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#9ca3af',
          formatter: function (value: number) {
            return formatCurrency(value, currency);
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
  }, [labels, preferences.currency]);

  const barChartData = useMemo(() => {
    return {
      series: [
        {
          name: 'Budget',
          type: 'bar',
          data: monthlyData.map((m) => m.total_budget),
          barMaxWidth: 24,
          itemStyle: {
            color: '#3b82f6',
            borderRadius: [4, 4, 0, 0],
          },
        },
        {
          name: 'Spent',
          type: 'bar',
          data: monthlyData.map((m) => m.total_spent),
          barMaxWidth: 24,
          itemStyle: {
            color: function (params: { dataIndex: number }) {
              const spent = monthlyData[params.dataIndex]?.total_spent || 0;
              const budget = monthlyData[params.dataIndex]?.total_budget || 0;
              if (spent > budget) return '#ef4444';
              if (spent > budget * 0.8) return '#f59e0b';
              return '#10b981';
            },
            borderRadius: [4, 4, 0, 0],
          },
        },
      ],
    };
  }, [monthlyData]);

  const percentageChartOptions = useMemo(() => {
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params: Array<{ name?: string; color?: string; value?: number | number[] }>) {
          const p = params?.[0];
          if (!p) return '';
          const value = Array.isArray(p.value) ? p.value[1] : p.value;
          return `${p.name}<br/><span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${p.color};"></span>Usage: ${value}%`;
        },
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: {
          color: '#9ca3af',
          fontSize: 11,
        },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: function (value: { max: number }) {
          return Math.max(100, Math.ceil(value.max / 10) * 10);
        },
        axisLabel: {
          color: '#9ca3af',
          formatter: '{value}%',
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true,
      },
      visualMap: {
        show: false,
        pieces: [
          { lte: 80, color: '#10b981' },
          { gt: 80, lte: 100, color: '#f59e0b' },
          { gt: 100, color: '#ef4444' },
        ],
      },
      markLine: {
        silent: true,
        data: [
          {
            yAxis: 100,
            lineStyle: { color: '#ef4444', type: 'dashed' },
            label: { formatter: '100%', color: '#ef4444' },
          },
        ],
      },
    };
  }, [labels]);

  const percentageChartData = useMemo(() => {
    return {
      series: [
        {
          name: 'Usage',
          type: 'line',
          data: monthlyData.map((m) => m.percentage),
          smooth: true,
          lineStyle: { width: 3 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
              ],
            },
          },
          markLine: {
            silent: true,
            symbol: 'none',
            data: [
              {
                yAxis: 100,
                lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
                label: {
                  formatter: 'Budget Limit',
                  position: 'end',
                  color: '#ef4444',
                },
              },
            ],
          },
        },
      ],
    };
  }, [monthlyData]);

  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Budget Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!monthlyData || monthlyData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">No trend data available</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getChartData = () => {
    switch (activeView) {
      case 'line':
        return { data: lineChartData, options: lineChartOptions };
      case 'bar':
        return { data: barChartData, options: barChartOptions };
      case 'percentage':
        return { data: percentageChartData, options: percentageChartOptions };
      default:
        return { data: barChartData, options: barChartOptions };
    }
  };

  const { data, options } = getChartData();

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Budget Trends</CardTitle>
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          <button
            onClick={() => setActiveView('bar')}
            className={`p-2 rounded transition-colors ${
              activeView === 'bar'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Bar Chart"
          >
            <BarChart3 className="h-4 w-4" />
          </button>
          <button
            onClick={() => setActiveView('line')}
            className={`p-2 rounded transition-colors ${
              activeView === 'line'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Line Chart"
          >
            <LineChart className="h-4 w-4" />
          </button>
          <button
            onClick={() => setActiveView('percentage')}
            className={`p-2 rounded transition-colors ${
              activeView === 'percentage'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Percentage Chart"
          >
            <Percent className="h-4 w-4" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <BaseChart
          type={activeView === 'bar' ? 'bar' : 'line'}
          data={data}
          options={options}
          height="280px"
        />
      </CardContent>
    </Card>
  );
}
