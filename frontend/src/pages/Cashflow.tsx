import { IncomeExpenseChart } from '@/components/asset_dashboard/IncomeExpenseChart';
import { Card, CardContent } from '@/components/ui/card';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import { Category, transactionsApiService } from '@/lib/api/transactions';
import ReactECharts from 'echarts-for-react';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useEffect, useState } from 'react';

// Function to get computed CSS values
const getCSSValue = (property: string) => {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
};

// Color palette for the Sankey diagram
const COLORS = {
  income: '#22c55e', // green-500
  incomeLight: '#86efac', // green-300
  expense: '#ef4444', // red-500
  expenseLight: '#fca5a5', // red-300
  investment: '#3b82f6', // blue-500
  investmentLight: '#93c5fd', // blue-300
  savings: '#eab308', // yellow-500
  savingsLight: '#fde047', // yellow-300
  neutral: '#6b7280', // gray-500
};

interface CashflowData {
  totalIncome: number;
  totalExpenses: number;
  totalInvestments: number;
  netSavings: number;
  incomeByCategory: Map<string, number>;
  expensesByCategory: Map<string, number>;
  investmentsByCategory: Map<string, number>;
}

export function Cashflow() {
  const [cashflowData, setCashflowData] = useState<CashflowData>({
    totalIncome: 0,
    totalExpenses: 0,
    totalInvestments: 0,
    netSavings: 0,
    incomeByCategory: new Map(),
    expensesByCategory: new Map(),
    investmentsByCategory: new Map(),
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [themeKey, setThemeKey] = useState(0);

  // Year and month state for date filtering
  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);

  const handleDateChange = (newYear: number, newMonth: number) => {
    setYear(newYear);
    setMonth(newMonth);
  };

  // Build category hierarchy map
  const buildCategoryMap = (
    cats: Category[]
  ): Map<
    number,
    { name: string; parentId: number | null; parentName: string | null }
  > => {
    const map = new Map<
      number,
      { name: string; parentId: number | null; parentName: string | null }
    >();
    cats.forEach(cat => {
      map.set(cat.id, {
        name: cat.name,
        parentId: cat.parent || null,
        parentName: cat.parent_name || null,
      });
    });
    return map;
  };

  // Check if a category is an investment category
  const isInvestmentCategory = (
    categoryName: string | null,
    categoryId: number | null,
    categoryMap: Map<
      number,
      { name: string; parentId: number | null; parentName: string | null }
    >
  ): boolean => {
    if (!categoryName) return false;
    const lowerName = categoryName.toLowerCase();

    // Direct match on investment-related keywords
    if (
      lowerName.includes('investment') ||
      lowerName.includes('401k') ||
      lowerName.includes('ira') ||
      lowerName.includes('stock') ||
      lowerName.includes('brokerage') ||
      lowerName.includes('retirement') ||
      lowerName.includes('crypto')
    ) {
      return true;
    }

    // Check parent category
    if (categoryId && categoryMap.has(categoryId)) {
      const cat = categoryMap.get(categoryId)!;
      if (cat.parentName) {
        const parentLower = cat.parentName.toLowerCase();
        if (
          parentLower.includes('investment') ||
          parentLower.includes('retirement')
        ) {
          return true;
        }
      }
    }

    return false;
  };

  // Fetch real data from APIs
  const fetchCashflowData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Compute date range from year and month
      const pad2 = (n: number) => String(n).padStart(2, '0');
      const startDate = `${year}-${pad2(month)}-01`;
      const endOfMonth = new Date(year, month, 0);
      const endDate = `${endOfMonth.getFullYear()}-${pad2(endOfMonth.getMonth() + 1)}-${pad2(endOfMonth.getDate())}`;

      // Fetch all data in parallel
      const [incomeTransactions, expenseTransactions, categoriesData] =
        await Promise.all([
          transactionsApiService.getIncomeTransactions({ startDate, endDate }),
          transactionsApiService.getExpenseTransactions({ startDate, endDate }),
          transactionsApiService.getCategories(),
        ]);

      const categoryMap = buildCategoryMap(categoriesData);

      // Group income by category (not by account)
      const incomeByCategory = new Map<string, number>();
      let totalIncome = 0;

      incomeTransactions.forEach(tx => {
        const categoryName = tx.category_name || 'Other Income';
        const amount = Number(tx.amount);
        totalIncome += amount;
        incomeByCategory.set(
          categoryName,
          (incomeByCategory.get(categoryName) || 0) + amount
        );
      });

      // Group expenses and investments by category (simple flat structure)
      const expensesByCategory = new Map<string, number>();
      const investmentsByCategory = new Map<string, number>();

      let totalExpenses = 0;
      let totalInvestments = 0;

      expenseTransactions.forEach(tx => {
        const amount = Number(tx.amount);
        const categoryName = tx.category_name || 'Uncategorized';
        const isInvestment = isInvestmentCategory(
          categoryName,
          tx.category,
          categoryMap
        );

        if (isInvestment) {
          totalInvestments += amount;
          investmentsByCategory.set(
            categoryName,
            (investmentsByCategory.get(categoryName) || 0) + amount
          );
        } else {
          totalExpenses += amount;
          expensesByCategory.set(
            categoryName,
            (expensesByCategory.get(categoryName) || 0) + amount
          );
        }
      });

      const netSavings = totalIncome - totalExpenses - totalInvestments;

      setCashflowData({
        totalIncome,
        totalExpenses,
        totalInvestments,
        netSavings,
        incomeByCategory,
        expensesByCategory,
        investmentsByCategory,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load cashflow data'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCashflowData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, month]);

  // Listen for theme changes
  useEffect(() => {
    const handleThemeChange = () => {
      setThemeKey(prev => prev + 1);
    };

    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'class'
        ) {
          handleThemeChange();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, []);

  const getSankeyOption = () => {
    const sankeyText =
      getCSSValue('--sankey-text') || getCSSValue('--foreground');
    const sankeyBg = getCSSValue('--sankey-bg') || getCSSValue('--card');
    const sankeyBorder =
      getCSSValue('--sankey-border') || getCSSValue('--border');

    const nodes: Array<{ name: string; itemStyle: { color: string } }> = [];
    const links: Array<{ source: string; target: string; value: number }> = [];
    const nodeSet = new Set<string>();

    // Track which names are used at which level to avoid conflicts
    const usedNames = new Set<string>();

    const addNode = (name: string, color: string) => {
      if (!nodeSet.has(name)) {
        nodeSet.add(name);
        nodes.push({ name, itemStyle: { color } });
      }
    };

    // Level 1: Income Sources - prefix with "Income: " to avoid conflicts
    const incomeColors = [
      COLORS.income,
      COLORS.incomeLight,
      '#4ade80',
      '#16a34a',
    ];
    let incomeColorIndex = 0;
    const incomeNodeNames = new Map<string, string>();
    cashflowData.incomeByCategory.forEach((_value, name) => {
      const nodeName = `${name}`;
      incomeNodeNames.set(name, nodeName);
      usedNames.add(nodeName);
      const color = incomeColors[incomeColorIndex % incomeColors.length];
      addNode(nodeName, color);
      incomeColorIndex++;
    });

    // Level 2: Total Income (central node)
    addNode('Total Income', COLORS.income);
    usedNames.add('Total Income');

    // Level 3: Expense Categories
    const expenseColors = [
      COLORS.expense,
      COLORS.expenseLight,
      '#f87171',
      '#dc2626',
      '#b91c1c',
      '#991b1b',
      '#7f1d1d',
    ];
    let expenseColorIndex = 0;
    const expenseNodeNames = new Map<string, string>();

    cashflowData.expensesByCategory.forEach((_value, categoryName) => {
      let nodeName = categoryName;
      // Avoid conflicts with income sources
      if (usedNames.has(categoryName)) {
        nodeName = `${categoryName} (Expense)`;
      }
      expenseNodeNames.set(categoryName, nodeName);
      usedNames.add(nodeName);

      const color = expenseColors[expenseColorIndex % expenseColors.length];
      addNode(nodeName, color);
      expenseColorIndex++;
    });

    // Level 3: Investment Categories
    const investmentColors = [
      COLORS.investment,
      COLORS.investmentLight,
      '#60a5fa',
      '#2563eb',
    ];
    let investmentColorIndex = 0;
    const investmentNodeNames = new Map<string, string>();

    cashflowData.investmentsByCategory.forEach((_value, categoryName) => {
      let nodeName = categoryName;
      if (usedNames.has(categoryName)) {
        nodeName = `${categoryName} (Investment)`;
      }
      investmentNodeNames.set(categoryName, nodeName);
      usedNames.add(nodeName);

      const color =
        investmentColors[investmentColorIndex % investmentColors.length];
      addNode(nodeName, color);
      investmentColorIndex++;
    });

    // Add Net Savings node if positive
    if (cashflowData.netSavings > 0) {
      addNode('Net Savings', COLORS.savings);
    }

    // Links: Income Sources → Total Income
    cashflowData.incomeByCategory.forEach((value, name) => {
      if (value > 0) {
        const nodeName = incomeNodeNames.get(name) || name;
        links.push({ source: nodeName, target: 'Total Income', value });
      }
    });

    // Links: Total Income → Expense Categories
    cashflowData.expensesByCategory.forEach((value, categoryName) => {
      if (value > 0) {
        const nodeName = expenseNodeNames.get(categoryName) || categoryName;
        links.push({
          source: 'Total Income',
          target: nodeName,
          value,
        });
      }
    });

    // Links: Total Income → Investment Categories
    cashflowData.investmentsByCategory.forEach((value, categoryName) => {
      if (value > 0) {
        const nodeName = investmentNodeNames.get(categoryName) || categoryName;
        links.push({
          source: 'Total Income',
          target: nodeName,
          value,
        });
      }
    });

    // Links: Total Income → Net Savings
    if (cashflowData.netSavings > 0) {
      links.push({
        source: 'Total Income',
        target: 'Net Savings',
        value: cashflowData.netSavings,
      });
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: `hsl(${sankeyBg})`,
        borderColor: `hsl(${sankeyBorder})`,
        textStyle: {
          color: `hsl(${sankeyText})`,
        },
        formatter: (params: {
          dataType: 'node' | 'edge';
          data: {
            name?: string;
            value?: number;
            source?: string;
            target?: string;
          };
        }) => {
          if (params.dataType === 'node') {
            const value = params.data.value || 0;
            const percentage =
              cashflowData.totalIncome > 0
                ? ((value / cashflowData.totalIncome) * 100).toFixed(1)
                : 0;
            return `<strong>${params.data.name}</strong><br/>Amount: $${value.toLocaleString()}<br/>% of Income: ${percentage}%`;
          } else if (params.dataType === 'edge') {
            const percentage =
              cashflowData.totalIncome > 0
                ? (
                    ((params.data.value || 0) / cashflowData.totalIncome) *
                    100
                  ).toFixed(1)
                : 0;
            return `<strong>${params.data.source} → ${params.data.target}</strong><br/>Amount: $${(params.data.value || 0).toLocaleString()}<br/>% of Income: ${percentage}%`;
          }
          return '';
        },
      },
      series: [
        {
          type: 'sankey',
          data: nodes,
          links: links,
          emphasis: {
            focus: 'adjacency',
          },
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
            {
              depth: 3,
              itemStyle: { borderWidth: 0 },
              lineStyle: { opacity: 0.3 },
            },
          ],
          lineStyle: {
            color: 'gradient',
            curveness: 0.5,
          },
          itemStyle: {
            borderWidth: 1,
            borderColor: `hsl(${sankeyBorder})`,
          },
          label: {
            color: `hsl(${sankeyText})`,
            fontSize: 11,
            fontWeight: 500,
          },
          nodeAlign: 'justify',
          layoutIterations: 32,
        },
      ],
    };
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading cashflow data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">
            Error loading cashflow data: {error}
          </p>
          <button
            onClick={fetchCashflowData}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 mx-auto"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hasNoData =
    cashflowData.totalIncome === 0 && cashflowData.totalExpenses === 0;

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Floating Month/Year Picker */}
      <MonthYearPicker year={year} month={month} onChange={handleDateChange} />

      <div className="max-w-7xl mx-auto space-y-6">
        {hasNoData ? (
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardContent>
              <div className="text-center py-12">
                <div className="w-20 h-20 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                  <TrendingUp className="h-10 w-10 text-muted-foreground" />
                </div>
                <h2 className="text-2xl font-semibold text-foreground mb-2">
                  No Cashflow Data
                </h2>
                <p className="text-muted-foreground">
                  No income or expense transactions found for this month. Select
                  a different month using the picker.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Summary Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Income */}
              <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-500/20 rounded-lg">
                      <ArrowUpRight className="h-5 w-5 text-green-500" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Total Income
                      </p>
                      <p className="text-xl font-bold text-green-500">
                        {formatCurrency(cashflowData.totalIncome)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Total Expenses */}
              <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-500/20 rounded-lg">
                      <ArrowDownRight className="h-5 w-5 text-red-500" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Total Expenses
                      </p>
                      <p className="text-xl font-bold text-red-500">
                        {formatCurrency(cashflowData.totalExpenses)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Total Investments */}
              <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <Wallet className="h-5 w-5 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Investments
                      </p>
                      <p className="text-xl font-bold text-blue-500">
                        {formatCurrency(cashflowData.totalInvestments)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Net Savings */}
              <Card
                className={`bg-gradient-to-br ${
                  cashflowData.netSavings >= 0
                    ? 'from-yellow-500/10 to-yellow-600/5 border-yellow-500/20'
                    : 'from-orange-500/10 to-orange-600/5 border-orange-500/20'
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        cashflowData.netSavings >= 0
                          ? 'bg-yellow-500/20'
                          : 'bg-orange-500/20'
                      }`}
                    >
                      <PiggyBank
                        className={`h-5 w-5 ${
                          cashflowData.netSavings >= 0
                            ? 'text-yellow-500'
                            : 'text-orange-500'
                        }`}
                      />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Net Savings
                      </p>
                      <p
                        className={`text-xl font-bold ${
                          cashflowData.netSavings >= 0
                            ? 'text-yellow-500'
                            : 'text-orange-500'
                        }`}
                      >
                        {formatCurrency(cashflowData.netSavings)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sankey Diagram */}
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4 text-foreground">
                  Money Flow
                </h3>
                <div className="h-[500px]">
                  <ReactECharts
                    key={themeKey}
                    option={getSankeyOption()}
                    style={{ height: '100%', width: '100%' }}
                    opts={{ renderer: 'canvas' }}
                  />
                </div>
                <div className="flex flex-wrap gap-4 mt-4 justify-center text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS.income }}
                    />
                    <span className="text-muted-foreground">Income</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS.expense }}
                    />
                    <span className="text-muted-foreground">Expenses</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS.investment }}
                    />
                    <span className="text-muted-foreground">Investments</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS.savings }}
                    />
                    <span className="text-muted-foreground">Savings</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Income vs Expenses Chart (independent) */}
            <div className="lg:col-span-2 min-w-0 overflow-x-auto">
              <IncomeExpenseChart />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
