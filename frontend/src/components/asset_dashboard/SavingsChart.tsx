import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { assetDashboardApiService } from '@/lib/api/asset-dashboard';
import { AlertTriangle } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';

export function SavingsChart() {
  const [labels, setLabels] = useState<string[]>([]);
  const [series, setSeries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const fetchSavings = async () => {
    try {
      setError(null);
      const data = await assetDashboardApiService.getSavingsData();
      const nextLabels = data.labels || [];
      // Map datasets to ECharts series, preserving types/colors where possible
      const mappedSeries = (data.datasets || []).map((ds: any) => ({
        name: ds.label,
        type: ds.type || 'line',
        data: ds.data || [],
        smooth: ds.type ? undefined : true,
        areaStyle: ds.type
          ? undefined
          : {
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
        lineStyle: ds.borderColor
          ? { color: ds.borderColor, width: 2 }
          : undefined,
        itemStyle: ds.backgroundColor
          ? { color: ds.backgroundColor }
          : undefined,
        barMaxWidth: ds.type === 'bar' ? 24 : undefined,
      }));
      // If all values are zero or empty, treat as no data
      const allValues = (mappedSeries || [])
        .flatMap((s: any) => s.data as number[])
        .filter(v => typeof v === 'number');
      const hasNonZero = allValues.some(v => v !== 0);

      if (!nextLabels.length || !hasNonZero) {
        setLabels([]);
        setSeries([]);
      } else {
        setLabels(nextLabels);
        setSeries(mappedSeries);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load savings data'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavings();

    // Poll every 30 seconds
    intervalRef.current = window.setInterval(fetchSavings, 30000);
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, []);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        formatter: function (params: any) {
          const lines = (params || []).map((p: any) => {
            const value = Array.isArray(p.value) ? p.value[1] : p.value;
            return `${p.seriesName}: $${Number(value ?? 0).toLocaleString()}`;
          });
          const name = params?.[0]?.name ?? '';
          return [name, ...lines].join('<br/>');
        },
      },
      xAxis: {
        type: 'category',
        data: labels,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: function (value: number) {
            return '$' + Number(value ?? 0).toLocaleString();
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
    }),
    [labels]
  );

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Savings Accumulation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">Loading...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Savings Accumulation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchSavings}
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

  if (!series.length || !labels.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Savings Accumulation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">
              No savings data available
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Savings Accumulation</CardTitle>
      </CardHeader>
      <CardContent>
        <BaseChart type="line" data={{ series }} options={chartOptions} />
      </CardContent>
    </Card>
  );
}
