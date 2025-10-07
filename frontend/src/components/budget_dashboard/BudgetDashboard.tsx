import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBudgetDateRange } from '@/contexts/BudgetDateRangeContext';
import { dashboardApiService } from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { CategoryBreakdown } from './CategoryBreakdown';
import { PieWithDetailedLegend } from './PieWithDetailedLegend';

interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
  remaining: number;
}

// Function to get computed CSS values
const getCSSValue = (property: string) => {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
};

export function BudgetDashboard() {
  const { startDate, endDate, setRange } = useBudgetDateRange();
  const [budgetCategories, setBudgetCategories] = useState<BudgetCategory[]>(
    []
  );
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [years, setYears] = useState<number[]>([]);
  const [fromYear, setFromYear] = useState<number | null>(null);
  const [fromMonth, setFromMonth] = useState<number | null>(null);
  const [toYear, setToYear] = useState<number | null>(null);
  const [toMonth, setToMonth] = useState<number | null>(null);

  // Fetch budget data from API
  const fetchBudgetData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch pre-aggregated budget progress from backend
      const { budgets: progress } =
        await transactionsApiService.getBudgetDashboard({
          startDate,
          endDate,
        });

      // Get chart colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');

      // Create budget categories from API response
      const categories: BudgetCategory[] = progress.map(
        (item: any, index: number) => ({
          name: item.category,
          budget: item.budget,
          spent: item.spent,
          percentage: item.percentage,
          color: `hsl(${[chart1, chart2, chart3, chart4, chart5, chart6][index % 6]})`,
          remaining: item.remaining,
        })
      );

      setBudgetCategories(categories);

      // Calculate totals
      const totalBudget = categories.reduce((sum, cat) => sum + cat.budget, 0);
      const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0);
      const totalRemaining = totalBudget - totalSpent;
      const overallPercentage =
        totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

      // Create chart data
      const chartDataObj = {
        series: [
          {
            name: 'Budget Usage',
            type: 'pie',
            radius: ['55%', '80%'],
            center: ['50%', '50%'],
            data: [
              {
                value: totalSpent,
                name: 'Spent',
                itemStyle: {
                  color: overallPercentage > 100 ? '#ef4444' : '#3b82f6',
                },
              },
              {
                value: Math.max(0, totalRemaining),
                name: 'Remaining',
                itemStyle: {
                  color: '#e5e7eb',
                },
              },
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)',
              },
            },
            label: {
              show: false,
            },
            labelLine: {
              show: false,
            },
          },
        ],
      };

      const chartOptionsObj = {
        tooltip: {
          trigger: 'item',
          formatter: function (params: any) {
            const value = params.value;
            const percentage =
              totalBudget > 0 ? Math.round((value / totalBudget) * 100) : 0;
            return `${params.name}: $${value.toLocaleString()} (${percentage}%)`;
          },
        },
        legend: {
          show: false,
        },
      };

      setChartData(chartDataObj);
      setChartOptions(chartOptionsObj);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load budget data'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initialize years/month to current if available
    const init = async () => {
      try {
        const yrs = await dashboardApiService.getExpenseYears();
        setYears(yrs);
        const startParts = startDate.split('-');
        const endParts = endDate.split('-');
        const fy = Number(startParts[0]);
        const fm = Number(startParts[1]);
        const ty = Number(endParts[0]);
        const tm = Number(endParts[1]);
        setFromYear(fy);
        setFromMonth(fm);
        setToYear(ty);
        setToMonth(tm);
        await fetchBudgetData();
      } catch (e) {
        // fallback without filters
        await fetchBudgetData();
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pad2 = (n: number) => String(n).padStart(2, '0');
  const computeEndOfMonth = (year: number, month: number) => {
    const end = new Date(year, month, 0);
    return `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())}`;
  };

  const updateRangeAndFetch = async (
    yFrom: number,
    mFrom: number,
    yTo: number,
    mTo: number
  ) => {
    const start = `${yFrom}-${pad2(mFrom)}-01`;
    const endStr = computeEndOfMonth(yTo, mTo);
    setRange({ startDate: start, endDate: endStr });
    await fetchBudgetData();
  };

  const handleFromYearChange = async (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const y = Number(e.target.value);
    setFromYear(y);
    const m = fromMonth ?? 1;
    await updateRangeAndFetch(y, m, toYear ?? y, toMonth ?? m);
  };

  const handleFromMonthChange = async (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const m = Number(e.target.value);
    setFromMonth(m);
    const y = fromYear ?? new Date().getFullYear();
    await updateRangeAndFetch(y, m, toYear ?? y, toMonth ?? m);
  };

  const handleToYearChange = async (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const y = Number(e.target.value);
    setToYear(y);
    const m = toMonth ?? 12;
    await updateRangeAndFetch(fromYear ?? y, fromMonth ?? 1, y, m);
  };

  const handleToMonthChange = async (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const m = Number(e.target.value);
    setToMonth(m);
    const y = toYear ?? new Date().getFullYear();
    await updateRangeAndFetch(fromYear ?? y, fromMonth ?? 1, y, m);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent className="overflow-y-hidden">
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
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent className="overflow-y-hidden">
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={() => fetchBudgetData()}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 mx-auto"
              >
                Retry
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!chartData || !chartOptions) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Budget Overview</CardTitle>
        </CardHeader>
        <CardContent className="overflow-y-hidden">
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">
              No budget data available
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate totals for display
  const totalBudget = budgetCategories.reduce(
    (sum, cat) => sum + cat.budget,
    0
  );
  const totalSpent = budgetCategories.reduce((sum, cat) => sum + cat.spent, 0);
  const overallPercentage =
    totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

  return (
    <div>
      <div className="flex items-center flex-wrap gap-2 mb-2">
        <span className="text-sm text-muted-foreground mr-1">From</span>
        <select
          className="border rounded px-2 py-1 bg-background"
          value={fromYear ?? ''}
          onChange={handleFromYearChange}
        >
          <option value="" disabled>
            Year
          </option>
          {(years.length ? years : [new Date().getFullYear()]).map(y => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          className="border rounded px-2 py-1 bg-background"
          value={fromMonth ?? ''}
          onChange={handleFromMonthChange}
        >
          <option value="" disabled>
            Month
          </option>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
            <option key={m} value={m}>
              {new Date(2000, m - 1, 1).toLocaleString('default', {
                month: 'short',
              })}
            </option>
          ))}
        </select>
        <span className="text-sm text-muted-foreground mx-1">to</span>
        <select
          className="border rounded px-2 py-1 bg-background"
          value={toYear ?? ''}
          onChange={handleToYearChange}
        >
          <option value="" disabled>
            Year
          </option>
          {(years.length ? years : [new Date().getFullYear()]).map(y => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          className="border rounded px-2 py-1 bg-background"
          value={toMonth ?? ''}
          onChange={handleToMonthChange}
        >
          <option value="" disabled>
            Month
          </option>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
            <option key={m} value={m}>
              {new Date(2000, m - 1, 1).toLocaleString('default', {
                month: 'short',
              })}
            </option>
          ))}
        </select>
      </div>
      <PieWithDetailedLegend
        title="Budget Overview"
        info={
          <div className="space-y-2">
            <p className="text-foreground">
              Overall Usage = Total Spent / Total Budget.
            </p>
            <p>
              Total Spent and Total Budget are summed across all categories for
              the selected period. Remaining = Total Budget - Total Spent.
            </p>
          </div>
        }
        chartData={chartData}
        chartOptions={chartOptions}
        centerPrimary={`${overallPercentage}%`}
        centerSecondaryLabel="Used"
        centerTertiaryLabel={`$${totalSpent.toLocaleString()} / $${totalBudget.toLocaleString()}`}
        legend={<CategoryBreakdown categories={budgetCategories} />}
        height="20rem"
      />
    </div>
  );
}
