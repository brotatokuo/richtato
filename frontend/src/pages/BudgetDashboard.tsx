import { MetricCard } from '@/components/asset_dashboard/MetricCard';
import { BudgetDashboard } from '@/components/budget_dashboard/BudgetBreakdown';
import { ExpenseBreakdown } from '@/components/budget_dashboard/ExpenseBreakdown';
import {
  BudgetDateRangeProvider,
  useBudgetDateRange,
} from '@/contexts/BudgetDateRangeContext';
import { budgetDashboardApiService } from '@/lib/api/budget-dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertTriangle, Gauge, Percent } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// Removed non-dropdown global date inputs; dropdown range is inside BudgetDashboard

export function Dashboard() {
  return (
    <BudgetDateRangeProvider>
      <DashboardContent />
    </BudgetDateRangeProvider>
  );
}

function MonthYearControls({
  onChange,
}: {
  onChange: (year: number, month: number) => void;
}) {
  const years = useMemo(() => {
    const current = new Date().getFullYear();
    // reasonable range; could be fetched but keeping local for simplicity
    const arr: number[] = [];
    for (let y = current; y >= current - 15; y--) arr.push(y);
    return arr;
  }, []);
  const { startDate } = useBudgetDateRange();
  const [year, setYear] = useState<number>(() =>
    Number(startDate.split('-')[0])
  );
  const [month, setMonth] = useState<number>(() =>
    Number(startDate.split('-')[1])
  );

  const handleYear = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const y = Number(e.target.value);
    setYear(y);
    onChange(y, month);
  };
  const handleMonth = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const m = Number(e.target.value);
    setMonth(m);
    onChange(year, m);
  };
  return (
    <div className="flex items-center flex-wrap gap-3">
      <select
        className="border rounded-md px-3 py-2 bg-background text-lg"
        value={year}
        onChange={handleYear}
      >
        {years.map(y => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
      <select
        className="border rounded-md px-3 py-2 bg-background text-lg"
        value={month}
        onChange={handleMonth}
      >
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
          <option key={m} value={m}>
            {new Date(2000, m - 1, 1).toLocaleString('default', {
              month: 'short',
            })}
          </option>
        ))}
      </select>
    </div>
  );
}

function DashboardContent() {
  const { startDate, endDate, setRange } = useBudgetDateRange();
  const [budgetUtilizationPct, setBudgetUtilizationPct] =
    useState<string>('N/A');
  const [nonEssentialPct, setNonEssentialPct] = useState<string>('N/A');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [budgetProgress, setBudgetProgress] = useState<
    Array<{
      category: string;
      budget: number;
      spent: number;
      percentage: number;
      remaining: number;
      year: number;
      month: number;
    }>
  >([]);
  const lastRangeRef = useRef<string | null>(null);

  const loadAllDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [budgetProgressData, categories, expenseData] = await Promise.all([
        budgetDashboardApiService.getBudgetProgress({
          startDate,
          endDate,
        }),
        transactionsApiService.getCategories(),
        budgetDashboardApiService.getExpenseCategoriesData({
          startDate,
          endDate,
        }),
      ]);

      // Set budget progress
      setBudgetProgress(budgetProgressData.budgets);

      // Calculate budget utilization
      const totalBudget = budgetProgressData.budgets.reduce(
        (sum: number, b: any) => sum + (b.budget || 0),
        0
      );
      const totalSpent = budgetProgressData.budgets.reduce(
        (sum: number, b: any) => sum + (b.spent || 0),
        0
      );
      const budgetPct =
        totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;
      setBudgetUtilizationPct(`${budgetPct}%`);

      // Calculate non-essential spending percentage
      const nonEssentialNames = new Set(
        categories
          .filter((c: any) => c.type === 'nonessential')
          .map((c: any) => c.name)
      );
      const labels: string[] = expenseData.labels || [];
      const values: number[] =
        (expenseData.datasets?.[0]?.data as number[]) || [];
      let total = 0;
      let nonEssential = 0;
      for (let i = 0; i < labels.length; i++) {
        const v = Number(values[i] || 0);
        total += v;
        if (nonEssentialNames.has(labels[i])) nonEssential += v;
      }
      const nonEssentialPctValue =
        total > 0 ? Math.round((nonEssential / total) * 100) : 0;
      setNonEssentialPct(`${nonEssentialPctValue}%`);

      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setLoading(false);
    }
  }, [startDate, endDate]);

  // Load all data when date range changes
  useEffect(() => {
    // Deduplicate same-range fetches (avoids StrictMode double-invoke)
    const key = `${startDate}|${endDate}`;
    if (lastRangeRef.current === key) return;
    lastRangeRef.current = key;

    loadAllDashboardData();
  }, [startDate, endDate, loadAllDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600 mb-4">Error loading dashboard: {error}</p>
          <button
            onClick={loadAllDashboardData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-full">
      {/* Global Month/Year Controls */}
      <div className="flex justify-start">
        <MonthYearControls
          onChange={(y, m) => {
            const pad2 = (n: number) => String(n).padStart(2, '0');
            const start = `${y}-${pad2(m)}-01`;
            const end = new Date(y, m, 0);
            const endStr = `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())}`;
            setRange({ startDate: start, endDate: endStr });
          }}
        />
      </div>

      {/* KPI Summary Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 min-w-0">
        <MetricCard
          title="Budget Utilization"
          value={budgetUtilizationPct}
          subtitle="of selected period"
          icon={<Gauge className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Budget Utilization = Total Spent / Total Budget.
              </p>
              <p>
                Totals are summed across all categories for the selected period.
              </p>
            </div>
          }
        />

        <MetricCard
          title="Non-Essential Spending"
          value={nonEssentialPct}
          subtitle="of total spending"
          icon={<Percent className="h-4 w-4" />}
          info={
            <div className="space-y-2">
              <p className="text-foreground">
                Non‑Essential Spending = Non‑essential Expenses / Total
                Expenses.
              </p>
              <p>
                Categories flagged as non‑essential are included in the
                numerator for the selected period.
              </p>
            </div>
          }
        />
      </div>

      {/* Budget Progress */}
      <div className="lg:col-span-2 min-w-0 overflow-x-auto">
        <BudgetDashboard progress={budgetProgress} />
      </div>

      {/* Main Analytics Grid */}
      <div className="grid gap-6 lg:grid-cols-2 min-w-0">
        {/* Expense Breakdown */}
        <div className="lg:col-span-2 min-w-0 overflow-x-auto">
          <ExpenseBreakdown />
        </div>
      </div>
    </div>
  );
}
