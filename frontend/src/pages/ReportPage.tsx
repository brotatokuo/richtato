import { IncomeExpenseChart } from '@/components/asset_dashboard/IncomeExpenseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import { YearPicker } from '@/components/ui/YearPicker';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  annualAnalysisApiService,
  type CategoryBreakdown,
  type IncomeSource,
} from '@/lib/api/annual-analysis';
import { transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency } from '@/lib/format';
import echarts, { type ECharts, type EChartsOption } from '@/lib/echarts';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  PiggyBank,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

type TimeScope = 'month' | 'year';

const COLORS = {
  income: '#22c55e',
  expense: '#ef4444',
  investment: '#3b82f6',
  savings: '#eab308',
};

interface NormalizedData {
  totalIncome: number;
  totalExpenses: number;
  totalInvestments: number;
  netSavings: number;
  savingsRate: number;
  incomeByCategory: Map<string, number>;
  expensesByCategory: Map<string, number>;
  investmentsByCategory: Map<string, number>;
  categoryBreakdown: CategoryBreakdown[];
  incomeSources: IncomeSource[];
}

function getCSSValue(property: string) {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
}

export function ReportPage() {
  const { preferences } = usePreferences();
  const [scope, setScope] = useState<TimeScope>('month');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Month mode state
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [monthYear, setMonthYear] = useState(now.getFullYear());

  // Year mode state
  const [selectedYear, setSelectedYear] = useState(now.getFullYear());
  const [availableYears, setAvailableYears] = useState<number[]>([]);

  const [data, setData] = useState<NormalizedData | null>(null);

  // Sankey chart refs
  const sankeyChartRef = useRef<HTMLDivElement>(null);
  const sankeyChartInstance = useRef<ECharts | null>(null);

  const loadMonthData = useCallback(async () => {
    const pad = (n: number) => String(n).padStart(2, '0');
    const startDate = `${monthYear}-${pad(month)}-01`;
    const endOfMonth = new Date(monthYear, month, 0);
    const endDate = `${endOfMonth.getFullYear()}-${pad(endOfMonth.getMonth() + 1)}-${pad(endOfMonth.getDate())}`;

    const summary = await transactionsApiService.getCashflowSummary(
      startDate,
      endDate
    );

    const incomeByCategory = new Map(
      Object.entries(summary.income_by_category)
    );
    const expensesByCategory = new Map(
      Object.entries(summary.expenses_by_category)
    );
    const investmentsByCategory = new Map(
      Object.entries(summary.investments_by_category)
    );

    const categoryBreakdown: CategoryBreakdown[] = [
      ...Array.from(expensesByCategory.entries()).map(([name, amount]) => ({
        name,
        amount,
        is_essential: false,
        color: COLORS.expense,
        icon: '',
      })),
      ...Array.from(investmentsByCategory.entries()).map(([name, amount]) => ({
        name,
        amount,
        is_essential: false,
        color: COLORS.investment,
        icon: '',
      })),
    ];

    const incomeSources: IncomeSource[] = Array.from(
      incomeByCategory.entries()
    ).map(([name, amount]) => ({
      name,
      amount,
      color: COLORS.income,
    }));

    setData({
      totalIncome: summary.total_income,
      totalExpenses: summary.total_expenses,
      totalInvestments: summary.total_investments,
      netSavings: summary.net_savings,
      savingsRate:
        summary.total_income > 0
          ? Math.round((summary.net_savings / summary.total_income) * 100)
          : 0,
      incomeByCategory,
      expensesByCategory,
      investmentsByCategory,
      categoryBreakdown,
      incomeSources,
    });
  }, [month, monthYear]);

  const loadYearData = useCallback(async () => {
    const [analysisData, years] = await Promise.all([
      annualAnalysisApiService.getAnnualAnalysis(selectedYear),
      annualAnalysisApiService.getAvailableYears(),
    ]);

    setAvailableYears(years.length > 0 ? years : [now.getFullYear()]);

    const expensesByCategory = new Map<string, number>();
    const investmentsByCategory = new Map<string, number>();

    analysisData.category_breakdown.forEach(cat => {
      expensesByCategory.set(cat.name, cat.amount);
    });

    const incomeByCategory = new Map<string, number>();
    analysisData.income_sources.forEach(s => {
      incomeByCategory.set(s.name, s.amount);
    });

    setData({
      totalIncome: analysisData.total_income,
      totalExpenses: analysisData.total_expenses,
      totalInvestments: 0,
      netSavings: analysisData.net_savings,
      savingsRate: analysisData.savings_rate,
      incomeByCategory,
      expensesByCategory,
      investmentsByCategory,
      categoryBreakdown: analysisData.category_breakdown,
      incomeSources: analysisData.income_sources,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedYear]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        if (scope === 'month') {
          await loadMonthData();
        } else {
          await loadYearData();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [scope, loadMonthData, loadYearData]);

  // Sankey chart
  useEffect(() => {
    if (!sankeyChartRef.current || !data) return;

    if (sankeyChartInstance.current) {
      sankeyChartInstance.current.dispose();
    }

    sankeyChartInstance.current = echarts.init(sankeyChartRef.current);

    const sankeyText =
      getCSSValue('--sankey-text') || getCSSValue('--foreground');
    const sankeyBg = getCSSValue('--sankey-bg') || getCSSValue('--card');
    const sankeyBorder =
      getCSSValue('--sankey-border') || getCSSValue('--border');

    const nodes: Array<{ name: string; itemStyle: { color: string } }> = [];
    const links: Array<{ source: string; target: string; value: number }> = [];
    const nodeSet = new Set<string>();
    const usedNames = new Set<string>();

    const addNode = (name: string, color: string) => {
      if (!nodeSet.has(name)) {
        nodeSet.add(name);
        nodes.push({ name, itemStyle: { color } });
      }
    };

    // Income sources
    const incomeColors = ['#22c55e', '#86efac', '#4ade80', '#16a34a'];
    let ci = 0;
    const incomeNodeNames = new Map<string, string>();
    data.incomeByCategory.forEach((_v, name) => {
      incomeNodeNames.set(name, name);
      usedNames.add(name);
      addNode(name, incomeColors[ci % incomeColors.length]);
      ci++;
    });

    addNode('Total Income', COLORS.income);
    usedNames.add('Total Income');

    // Expense categories
    const expenseColors = [
      '#ef4444',
      '#fca5a5',
      '#f87171',
      '#dc2626',
      '#b91c1c',
      '#991b1b',
    ];
    let ei = 0;
    const expenseNodeNames = new Map<string, string>();
    data.expensesByCategory.forEach((_v, catName) => {
      let nodeName = catName;
      if (usedNames.has(catName)) nodeName = `${catName} (Expense)`;
      expenseNodeNames.set(catName, nodeName);
      usedNames.add(nodeName);
      addNode(nodeName, expenseColors[ei % expenseColors.length]);
      ei++;
    });

    // Investment categories
    const investColors = ['#3b82f6', '#93c5fd', '#60a5fa', '#2563eb'];
    let ii = 0;
    const investNodeNames = new Map<string, string>();
    data.investmentsByCategory.forEach((_v, catName) => {
      let nodeName = catName;
      if (usedNames.has(catName)) nodeName = `${catName} (Investment)`;
      investNodeNames.set(catName, nodeName);
      usedNames.add(nodeName);
      addNode(nodeName, investColors[ii % investColors.length]);
      ii++;
    });

    if (data.netSavings > 0) {
      addNode('Net Savings', COLORS.savings);
    }

    // Links: Income → Total Income
    data.incomeByCategory.forEach((value, name) => {
      if (value > 0)
        links.push({
          source: incomeNodeNames.get(name) || name,
          target: 'Total Income',
          value,
        });
    });

    // Links: Total Income → Expenses
    data.expensesByCategory.forEach((value, catName) => {
      if (value > 0)
        links.push({
          source: 'Total Income',
          target: expenseNodeNames.get(catName) || catName,
          value,
        });
    });

    // Links: Total Income → Investments
    data.investmentsByCategory.forEach((value, catName) => {
      if (value > 0)
        links.push({
          source: 'Total Income',
          target: investNodeNames.get(catName) || catName,
          value,
        });
    });

    if (data.netSavings > 0) {
      links.push({
        source: 'Total Income',
        target: 'Net Savings',
        value: data.netSavings,
      });
    }

    const option: EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: `hsl(${sankeyBg})`,
        borderColor: `hsl(${sankeyBorder})`,
        textStyle: { color: `hsl(${sankeyText})` },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const value = params.data.value || 0;
            const pct =
              data.totalIncome > 0
                ? ((value / data.totalIncome) * 100).toFixed(1)
                : '0';
            return `<strong>${params.data.name}</strong><br/>Amount: ${formatCurrency(value, preferences.currency)}<br/>% of Income: ${pct}%`;
          } else if (params.dataType === 'edge') {
            const pct =
              data.totalIncome > 0
                ? (((params.data.value || 0) / data.totalIncome) * 100).toFixed(
                    1
                  )
                : '0';
            return `<strong>${params.data.source} → ${params.data.target}</strong><br/>Amount: ${formatCurrency(params.data.value || 0, preferences.currency)}<br/>% of Income: ${pct}%`;
          }
          return '';
        },
      },
      series: [
        {
          type: 'sankey',
          data: nodes,
          links,
          emphasis: { focus: 'adjacency' },
          levels: [
            {
              depth: 0,
              itemStyle: { borderWidth: 0 },
              lineStyle: { opacity: 0.6 },
            },
            {
              depth: 1,
              itemStyle: { borderWidth: 0 },
              lineStyle: { opacity: 0.5 },
            },
            {
              depth: 2,
              itemStyle: { borderWidth: 0 },
              lineStyle: { opacity: 0.4 },
            },
          ],
          lineStyle: { color: 'gradient', curveness: 0.5 },
          itemStyle: { borderWidth: 1, borderColor: `hsl(${sankeyBorder})` },
          label: { color: `hsl(${sankeyText})`, fontSize: 11, fontWeight: 500 },
          nodeAlign: 'justify',
          layoutIterations: 32,
        },
      ],
    };

    sankeyChartInstance.current.setOption(option);
    return () => {
      sankeyChartInstance.current?.dispose();
    };
  }, [data, preferences.currency]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => sankeyChartInstance.current?.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertTriangle className="h-12 w-12 text-destructive" />
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const totalOutflow = data.totalExpenses + data.totalInvestments;

  return (
    <div className="space-y-6">
      {/* Time scope toggle + picker */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="inline-flex rounded-full border border-border/50 bg-muted/30 p-1">
          <button
            onClick={() => setScope('month')}
            className={cn(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
              scope === 'month'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Month
          </button>
          <button
            onClick={() => setScope('year')}
            className={cn(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
              scope === 'year'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Year
          </button>
        </div>
        {scope === 'month' ? (
          <MonthYearPicker
            year={monthYear}
            month={month}
            onChange={(y, m) => {
              setMonthYear(y);
              setMonth(m);
            }}
          />
        ) : (
          <YearPicker
            year={selectedYear}
            availableYears={availableYears}
            onChange={setSelectedYear}
          />
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Income</p>
                <p className="text-2xl font-bold text-green-500">
                  {formatCurrency(data.totalIncome, preferences.currency, 0)}
                </p>
              </div>
              <ArrowUpRight className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Expenses</p>
                <p className="text-2xl font-bold text-red-500">
                  {formatCurrency(totalOutflow, preferences.currency, 0)}
                </p>
              </div>
              <ArrowDownRight className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Net Savings</p>
                <p
                  className={cn(
                    'text-2xl font-bold',
                    data.netSavings >= 0 ? 'text-green-500' : 'text-red-500'
                  )}
                >
                  {formatCurrency(data.netSavings, preferences.currency, 0)}
                </p>
              </div>
              <PiggyBank
                className={cn(
                  'h-8 w-8',
                  data.netSavings >= 0 ? 'text-green-500' : 'text-red-500'
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Savings Rate</p>
                <p
                  className={cn(
                    'text-2xl font-bold',
                    data.savingsRate >= 20
                      ? 'text-green-500'
                      : data.savingsRate >= 0
                        ? 'text-yellow-500'
                        : 'text-red-500'
                  )}
                >
                  {data.savingsRate}%
                </p>
              </div>
              <TrendingUp
                className={cn(
                  'h-8 w-8',
                  data.savingsRate >= 0 ? 'text-green-500' : 'text-red-500'
                )}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Money Flow Sankey */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-lg">Money Flow</CardTitle>
        </CardHeader>
        <CardContent>
          {data.totalIncome === 0 && totalOutflow === 0 ? (
            <div className="flex h-80 items-center justify-center text-muted-foreground">
              No income or expense data for this period.
            </div>
          ) : (
            <>
              <div ref={sankeyChartRef} className="h-[420px]" />
              <div className="flex flex-wrap gap-4 mt-4 justify-center text-sm">
                {[
                  { color: COLORS.income, label: 'Income' },
                  { color: COLORS.expense, label: 'Expenses' },
                  { color: COLORS.investment, label: 'Investments' },
                  { color: COLORS.savings, label: 'Savings' },
                ].map(({ color, label }) => (
                  <div key={label} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-muted-foreground">{label}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Category Breakdown + Income vs Expenses */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Category Breakdown Table */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Category Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 overflow-y-auto">
              {data.categoryBreakdown.length === 0 ? (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  No spending data for this period.
                </div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-card">
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="pb-2 font-medium">Category</th>
                      <th className="pb-2 text-right font-medium">Amount</th>
                      <th className="pb-2 text-right font-medium">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...data.categoryBreakdown]
                      .sort((a, b) => b.amount - a.amount)
                      .map(category => {
                        const percentage =
                          totalOutflow > 0
                            ? (category.amount / totalOutflow) * 100
                            : 0;
                        return (
                          <tr
                            key={category.name}
                            className="border-b border-border/50 transition-colors hover:bg-muted/30"
                          >
                            <td className="py-2.5">
                              <div className="flex items-center gap-2">
                                <span className="text-base shrink-0">
                                  {category.icon || '📁'}
                                </span>
                                <span className="text-sm truncate">
                                  {category.name}
                                </span>
                              </div>
                            </td>
                            <td className="py-2.5 text-right text-sm tabular-nums">
                              {formatCurrency(
                                category.amount,
                                preferences.currency
                              )}
                            </td>
                            <td className="py-2.5 text-right text-sm text-muted-foreground tabular-nums">
                              {percentage.toFixed(1)}%
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Income vs Expenses over time */}
        <IncomeExpenseChart />
      </div>
    </div>
  );
}
