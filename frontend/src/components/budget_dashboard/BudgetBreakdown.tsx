import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBudgetDateRange } from '@/contexts/BudgetDateRangeContext';
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
  const { startDate, endDate } = useBudgetDateRange();
  const [budgetCategories, setBudgetCategories] = useState<BudgetCategory[]>(
    []
  );
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Initial load
  useEffect(() => {
    fetchBudgetData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refetch when global date range changes
  useEffect(() => {
    if (startDate && endDate) {
      fetchBudgetData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

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
