import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  assetDashboardApiService,
  NetWorthHistoryPoint,
} from '@/lib/api/asset-dashboard';
import { formatCurrency } from '@/lib/format';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { BaseChart } from './BaseChart';

type Period = '1m' | '3m' | '6m' | '1y' | 'all';

export function NetWorthTrendChart() {
  const { preferences } = usePreferences();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<NetWorthHistoryPoint[]>([]);
  const [period, setPeriod] = useState<Period>('6m');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assetDashboardApiService.getNetWorthHistory(period);
      setHistoryData(data.history || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load net worth history'
      );
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { chartSeries, dates } = useMemo(() => {
    if (historyData.length === 0) {
      return { chartSeries: [], dates: [] };
    }

    const sortedData = [...historyData].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const dateLabels = sortedData.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      dates: dateLabels,
      chartSeries: [
        {
          name: 'Net Worth',
          type: 'line',
          data: sortedData.map(d => d.networth),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 3,
            color: '#22c55e',
          },
          itemStyle: {
            color: '#22c55e',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
                { offset: 1, color: 'rgba(34, 197, 94, 0.05)' },
              ],
            },
          },
        },
        {
          name: 'Assets',
          type: 'line',
          data: sortedData.map(d => d.assets),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: '#3b82f6',
            type: 'dashed',
          },
          itemStyle: {
            color: '#3b82f6',
          },
        },
        {
          name: 'Liabilities',
          type: 'line',
          data: sortedData.map(d => d.liabilities),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: '#ef4444',
            type: 'dashed',
          },
          itemStyle: {
            color: '#ef4444',
          },
        },
      ],
    };
  }, [historyData]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: {
          color: '#f3f4f6',
        },
        formatter: function (params: Array<{ name?: string; value?: number; color?: string; seriesName?: string }>) {
          const date = params?.[0]?.name ?? '';
          const lines = (params || []).map((p) => {
            const value = p.value ?? 0;
            const color = p.color;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>${p.seriesName}: ${formatCurrency(value, preferences.currency)}`;
          });
          return [date, ...lines].join('<br/>');
        },
      },
      legend: {
        data: ['Net Worth', 'Assets', 'Liabilities'],
        bottom: 0,
        textStyle: {
          color: '#9ca3af',
        },
        icon: 'roundRect',
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          color: '#9ca3af',
          rotate: dates.length > 12 ? 45 : 0,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: function (value: number) {
            if (Math.abs(value) >= 1000000) {
              return `${(value / 1000000).toFixed(1)}M`;
            } else if (Math.abs(value) >= 1000) {
              return `${(value / 1000).toFixed(0)}K`;
            }
            return formatCurrency(value, preferences.currency, 0);
          },
          color: '#9ca3af',
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
    }),
    [dates, preferences.currency]
  );

  if (loading) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            Net Worth Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            Net Worth Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                Retry
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (historyData.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            Net Worth Trend
          </CardTitle>
          <Select value={period} onValueChange={v => setPeriod(v as Period)}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1m">1 Month</SelectItem>
              <SelectItem value="3m">3 Months</SelectItem>
              <SelectItem value="6m">6 Months</SelectItem>
              <SelectItem value="1y">1 Year</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p>No balance history available yet.</p>
              <p className="text-sm mt-1">
                Add balance updates to your accounts to track net worth over
                time.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="h-5 w-5 text-primary" />
          Net Worth Trend
        </CardTitle>
        <Select value={period} onValueChange={v => setPeriod(v as Period)}>
          <SelectTrigger className="w-24">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1m">1 Month</SelectItem>
            <SelectItem value="3m">3 Months</SelectItem>
            <SelectItem value="6m">6 Months</SelectItem>
            <SelectItem value="1y">1 Year</SelectItem>
            <SelectItem value="all">All Time</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <BaseChart
          type="line"
          data={{ series: chartSeries }}
          options={chartOptions}
          height={280}
        />
      </CardContent>
    </Card>
  );
}
