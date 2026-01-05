import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency } from '@/lib/format';
import { History, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { AccountGroup, AccountWithBalance } from './AccountsList';
import { BaseChart } from './BaseChart';

interface BalancePoint {
  date: string;
  balance: number;
}

interface AccountBalanceData {
  account: AccountWithBalance;
  history: BalancePoint[];
}

// Color palette for accounts
const ACCOUNT_COLORS = [
  '#22c55e', // green
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#84cc16', // lime
  '#ef4444', // red
  '#14b8a6', // teal
];

interface GroupHistoryPanelProps {
  group: AccountGroup;
  onClose: () => void;
}

export function GroupHistoryPanel({ group, onClose }: GroupHistoryPanelProps) {
  const { preferences } = usePreferences();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accountsData, setAccountsData] = useState<AccountBalanceData[]>([]);

  const fetchAllHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const promises = group.accounts.map(async account => {
        const data = await transactionsApiService.getAccountBalanceHistory(
          account.id
        );
        return {
          account,
          history: data?.data_points || [],
        };
      });

      const results = await Promise.all(promises);
      setAccountsData(results);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load balance history'
      );
    } finally {
      setLoading(false);
    }
  }, [group.accounts]);

  useEffect(() => {
    fetchAllHistory();
  }, [fetchAllHistory]);

  // Build chart data with all accounts
  const { chartSeries, dates } = useMemo(() => {
    if (accountsData.length === 0) {
      return { chartSeries: [], dates: [] };
    }

    // Collect all unique dates from all accounts
    const allDates = new Set<string>();
    accountsData.forEach(({ history }) => {
      history.forEach(h => allDates.add(h.date));
    });

    const sortedDates = Array.from(allDates).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );

    const dateLabels = sortedDates.map(d => {
      const date = new Date(d);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    });

    // Create a series for each account
    const series = accountsData.map(({ account, history }, index) => {
      // Build a map of date -> balance for this account
      const balanceMap = new Map<string, number>();
      history.forEach(h => {
        balanceMap.set(h.date, h.balance);
      });

      // For each date, find the most recent balance up to that date
      let lastKnownBalance = 0;
      const dataPoints = sortedDates.map(date => {
        if (balanceMap.has(date)) {
          lastKnownBalance = balanceMap.get(date)!;
        }
        return lastKnownBalance;
      });

      const color = ACCOUNT_COLORS[index % ACCOUNT_COLORS.length];

      return {
        name: account.name,
        type: 'line',
        data: dataPoints,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color,
        },
        itemStyle: {
          color,
        },
      };
    });

    return { chartSeries: series, dates: dateLabels };
  }, [accountsData]);

  // Calculate total series (sum of all accounts)
  const totalSeries = useMemo(() => {
    if (chartSeries.length === 0) return null;

    const totalData = chartSeries[0].data.map((_, i) =>
      chartSeries.reduce((sum, series) => sum + (series.data[i] || 0), 0)
    );

    return {
      name: 'Total',
      type: 'line',
      data: totalData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: '#ffffff',
        type: 'solid',
      },
      itemStyle: {
        color: '#ffffff',
        borderColor: '#374151',
        borderWidth: 2,
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255, 255, 255, 0.15)' },
            { offset: 1, color: 'rgba(255, 255, 255, 0.02)' },
          ],
        },
      },
    };
  }, [chartSeries]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: '#374151',
        textStyle: {
          color: '#f3f4f6',
        },
        formatter: function (
          params: Array<{ name?: string; value?: number; color?: string; seriesName?: string }>
        ) {
          const date = params?.[0]?.name ?? '';
          const lines = (params || []).map(p => {
            const value = p.value ?? 0;
            const color = p.color;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>${p.seriesName}: ${formatCurrency(value, preferences.currency)}`;
          });
          return [date, ...lines].join('<br/>');
        },
      },
      legend: {
        data: [...chartSeries.map(s => s.name), 'Total'],
        bottom: 0,
        textStyle: {
          color: '#9ca3af',
        },
        icon: 'circle',
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
            if (Math.abs(value) >= 1000) {
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
        bottom: '18%',
        top: '10%',
        containLabel: true,
      },
    }),
    [dates, chartSeries, preferences.currency]
  );

  const allSeries = totalSeries ? [...chartSeries, totalSeries] : chartSeries;

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 border-t-2 border-t-primary">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <History className="h-5 w-5 text-primary" />
            <div>
              <span className="text-lg">{group.typeDisplay}</span>
              <span className="text-sm font-normal text-muted-foreground ml-2">
                {group.accounts.length} account
                {group.accounts.length !== 1 && 's'} • Balance History
              </span>
            </div>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-600 mb-2">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchAllHistory}>
                Retry
              </Button>
            </div>
          </div>
        ) : chartSeries.length === 0 || dates.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No balance history for these accounts.</p>
              <p className="text-sm mt-1">
                Add balance updates to track changes over time.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <BaseChart
              type="line"
              data={{ series: allSeries }}
              options={chartOptions}
              height={300}
            />

            {/* Account summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {group.accounts.map((account, index) => (
                <div
                  key={account.id}
                  className="p-3 rounded-lg bg-muted/30 border border-border/50"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{
                        backgroundColor:
                          ACCOUNT_COLORS[index % ACCOUNT_COLORS.length],
                      }}
                    />
                    <span className="text-sm font-medium truncate">
                      {account.name}
                    </span>
                  </div>
                  <p
                    className={`text-lg font-semibold ${
                      account.balance >= 0 ? 'text-green-500' : 'text-red-500'
                    }`}
                  >
                    {formatCurrency(account.balance, preferences.currency)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
