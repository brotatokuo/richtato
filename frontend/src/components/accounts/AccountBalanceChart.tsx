import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency } from '@/lib/format';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AccountBalanceChartProps {
  accountId: number | null;
  accounts: Account[];
}

interface BalanceDataPoint {
  date: string;
  accountId: number;
  accountName: string;
  balance: number;
}

// Color palette for accounts (consistent with account types)
const ACCOUNT_COLORS = [
  '#22c55e', // green
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#84cc16', // lime
];

const getAccountColor = (index: number) => {
  return ACCOUNT_COLORS[index % ACCOUNT_COLORS.length];
};

export function AccountBalanceChart({
  accountId,
  accounts,
}: AccountBalanceChartProps) {
  const { preferences } = usePreferences();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [balanceData, setBalanceData] = useState<BalanceDataPoint[]>([]);

  const fetchBalanceHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      if (accountId === null) {
        // Fetch all accounts
        const promises = accounts.map(acc =>
          transactionsApiService.getAccountTransactions(acc.id, {
            page: 1,
            pageSize: 1000,
          })
        );
        const results = await Promise.all(promises);
        const allData: BalanceDataPoint[] = results.flatMap((r, idx) =>
          (r.rows || []).map((tx: any) => ({
            date: tx.date,
            accountId: accounts[idx].id,
            accountName: accounts[idx].name,
            balance: parseFloat(tx.amount) || 0,
          }))
        );
        setBalanceData(allData);
      } else {
        // Fetch single account
        const account = accounts.find(a => a.id === accountId);
        const data = await transactionsApiService.getAccountTransactions(
          accountId,
          { page: 1, pageSize: 1000 }
        );
        const txData: BalanceDataPoint[] = (data.rows || []).map((tx: any) => ({
          date: tx.date,
          accountId: accountId,
          accountName: account?.name || 'Account',
          balance: parseFloat(tx.amount) || 0,
        }));
        setBalanceData(txData);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load balance history'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accounts.length > 0) {
      fetchBalanceHistory();
    } else {
      setLoading(false);
    }
  }, [accountId, accounts]);

  // Transform data for ECharts stacked area chart
  const { chartSeries, dates } = useMemo(() => {
    if (balanceData.length === 0) {
      return { chartSeries: [], dates: [] };
    }

    // Get unique dates sorted
    const uniqueDates = Array.from(new Set(balanceData.map(d => d.date))).sort();

    // Get unique accounts in the data
    const accountsInData = accountId
      ? [{ id: accountId, name: accounts.find(a => a.id === accountId)?.name || 'Account' }]
      : accounts.filter(acc =>
          balanceData.some(d => d.accountId === acc.id)
        );

    // Create series for each account
    const series = accountsInData.map((acc, idx) => {
      // For each date, find the most recent balance for this account
      const dataByDate = uniqueDates.map(date => {
        // Find all balances for this account up to this date
        const accountBalances = balanceData
          .filter(d => d.accountId === acc.id && d.date <= date)
          .sort((a, b) => b.date.localeCompare(a.date));

        // Return the most recent balance, or 0 if none exists
        return accountBalances.length > 0 ? accountBalances[0].balance : 0;
      });

      return {
        name: acc.name,
        type: 'line',
        stack: 'Total',
        areaStyle: {
          opacity: 0.6,
        },
        emphasis: {
          focus: 'series',
        },
        smooth: true,
        data: dataByDate,
        itemStyle: {
          color: getAccountColor(idx),
        },
        lineStyle: {
          width: 2,
          color: getAccountColor(idx),
        },
      };
    });

    return { chartSeries: series, dates: uniqueDates };
  }, [balanceData, accountId, accounts]);

  const chartOptions = useMemo(
    () => ({
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985',
          },
        },
        formatter: function (params: any) {
          const date = params?.[0]?.name ?? '';
          const lines = (params || []).map((p: any) => {
            const value = p.value ?? 0;
            const color = p.color;
            return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>${p.seriesName}: ${formatCurrency(value, preferences.currency)}`;
          });
          // Add total
          const total = (params || []).reduce(
            (sum: number, p: any) => sum + (p.value ?? 0),
            0
          );
          lines.push(
            `<strong>Total: ${formatCurrency(total, preferences.currency)}</strong>`
          );
          return [date, ...lines].join('<br/>');
        },
      },
      legend: {
        data: chartSeries.map(s => s.name),
        bottom: 0,
        textStyle: {
          color: '#9ca3af',
        },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          color: '#9ca3af',
          rotate: dates.length > 10 ? 45 : 0,
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: function (value: number) {
            return formatCurrency(value, preferences.currency);
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
    [dates, chartSeries, preferences.currency]
  );

  const title = accountId
    ? `${accounts.find(a => a.id === accountId)?.name || 'Account'} Balance History`
    : 'All Accounts Balance History';

  if (loading) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">Loading chart...</div>
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
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchBalanceHistory}
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

  if (chartSeries.length === 0 || dates.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">
              No balance history available. Add balance updates to see the
              chart.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="h-5 w-5 text-primary" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <BaseChart
          type="line"
          data={{ series: chartSeries }}
          options={chartOptions}
          height={300}
        />
      </CardContent>
    </Card>
  );
}
