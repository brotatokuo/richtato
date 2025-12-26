import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  AccountBreakdownItem,
  assetDashboardApiService,
} from '@/lib/api/asset-dashboard';
import { formatCurrency } from '@/lib/format';
import { AlertTriangle, PieChart } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { BaseChart } from './BaseChart';

// Color palette for account types
const ACCOUNT_TYPE_COLORS: Record<string, string> = {
  checking: '#3b82f6', // blue
  savings: '#22c55e', // green
  credit_card: '#ef4444', // red
  investment: '#8b5cf6', // purple
  brokerage: '#f59e0b', // amber
  retirement: '#06b6d4', // cyan
};

const getAccountColor = (type: string): string => {
  return ACCOUNT_TYPE_COLORS[type] || '#6b7280';
};

export function AccountBreakdownChart() {
  const { preferences } = usePreferences();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [breakdownData, setBreakdownData] = useState<AccountBreakdownItem[]>(
    []
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assetDashboardApiService.getAccountBreakdown();
      setBreakdownData(data.breakdown || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load account breakdown'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Calculate totals
  const { totalAssets, totalLiabilities } = useMemo(() => {
    let assets = 0;
    let liabilities = 0;
    breakdownData.forEach(item => {
      if (item.is_liability) {
        liabilities += Math.abs(item.total);
      } else {
        assets += item.total;
      }
    });
    return { totalAssets: assets, totalLiabilities: liabilities };
  }, [breakdownData]);

  const chartData = useMemo(() => {
    if (breakdownData.length === 0) {
      return { series: [] };
    }

    // Filter to only positive values for donut chart
    const chartItems = breakdownData
      .filter(item => item.total > 0 || (item.is_liability && item.total !== 0))
      .map(item => ({
        name: item.type_display,
        value: Math.abs(item.total),
        itemStyle: {
          color: getAccountColor(item.type),
        },
      }));

    return {
      series: [
        {
          type: 'pie',
          radius: ['50%', '75%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          padAngle: 2,
          itemStyle: {
            borderRadius: 4,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#f3f4f6',
              formatter: function (params: any) {
                return `${params.name}\n${formatCurrency(params.value, preferences.currency)}`;
              },
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
          labelLine: {
            show: false,
          },
          data: chartItems,
        },
      ],
    };
  }, [breakdownData, preferences.currency]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: {
          color: '#f3f4f6',
        },
        formatter: function (params: any) {
          const value = params.value ?? 0;
          const percent = params.percent ?? 0;
          return `${params.name}<br/>${formatCurrency(value, preferences.currency)} (${percent.toFixed(1)}%)`;
        },
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        left: 'center',
        textStyle: {
          color: '#9ca3af',
        },
        icon: 'circle',
      },
    }),
    [preferences.currency]
  );

  if (loading) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <PieChart className="h-5 w-5 text-primary" />
            Account Breakdown
          </CardTitle>
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
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <PieChart className="h-5 w-5 text-primary" />
            Account Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
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

  if (breakdownData.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <PieChart className="h-5 w-5 text-primary" />
            Account Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p>No accounts found.</p>
              <p className="text-sm mt-1">Add accounts to see the breakdown.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <PieChart className="h-5 w-5 text-primary" />
          Account Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col">
          <BaseChart
            type="pie"
            data={chartData}
            options={chartOptions}
            height={200}
          />
          {/* Summary below chart */}
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
              <p className="text-muted-foreground">Total Assets</p>
              <p className="text-lg font-semibold text-green-500">
                {formatCurrency(totalAssets, preferences.currency)}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-muted-foreground">Total Liabilities</p>
              <p className="text-lg font-semibold text-red-500">
                {formatCurrency(totalLiabilities, preferences.currency)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
