import { IncomeExpenseChart } from '@/components/asset_dashboard/IncomeExpenseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CashFlowData, dashboardApiService } from '@/lib/api/dashboard';
import { transactionsApiService } from '@/lib/api/transactions';
import ReactECharts from 'echarts-for-react';
import { AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

// Function to get computed CSS values
const getCSSValue = (property: string) => {
  if (typeof window === 'undefined') return '';
  return getComputedStyle(document.documentElement)
    .getPropertyValue(property)
    .trim();
};

interface CashflowData {
  income: number;
  expenses: number;
  netFlow: number;
  categories: {
    income: Array<{ name: string; value: number; color: string }>;
    expenses: Array<{ name: string; value: number; color: string }>;
  };
}

export function Cashflow() {
  const [cashflowData, setCashflowData] = useState<CashflowData>({
    income: 0,
    expenses: 0,
    netFlow: 0,
    categories: {
      income: [],
      expenses: [],
    },
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [themeKey, setThemeKey] = useState(0); // Force re-render when theme changes
  const [incomeExpenseData, setIncomeExpenseData] =
    useState<CashFlowData | null>(null);

  // Fetch real data from APIs
  const fetchCashflowData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from APIs
      const [incomeTransactions, expenseTransactions, incomeVsExpenses] =
        await Promise.all([
          transactionsApiService.getIncomeTransactions(),
          transactionsApiService.getExpenseTransactions(),
          dashboardApiService.getIncomeExpensesData(),
        ]);

      // Get theme-aware colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');
      const chart7 = getCSSValue('--chart-7');

      // Calculate total income and expenses
      const totalIncome = incomeTransactions.reduce(
        (sum, transaction) => sum + transaction.amount,
        0
      );
      const totalExpenses = expenseTransactions.reduce(
        (sum, transaction) => sum + transaction.amount,
        0
      );
      const netFlow = totalIncome - totalExpenses;

      // Group income by source (using Account field as source)
      const incomeBySource = incomeTransactions.reduce(
        (acc, transaction) => {
          const source = transaction.Account || 'Unknown';
          if (!acc[source]) {
            acc[source] = 0;
          }
          acc[source] += transaction.amount;
          return acc;
        },
        {} as Record<string, number>
      );

      // Group expenses by category
      const expensesByCategory = expenseTransactions.reduce(
        (acc, transaction) => {
          const category = transaction.Category || 'Uncategorized';
          if (!acc[category]) {
            acc[category] = 0;
          }
          acc[category] += transaction.amount;
          return acc;
        },
        {} as Record<string, number>
      );

      // Convert to arrays with colors
      const incomeCategories = Object.entries(incomeBySource).map(
        ([name, value], index) => ({
          name,
          value,
          color: `hsl(${[chart1, chart2, chart3, chart4][index % 4]})`,
        })
      );

      const expenseCategories = Object.entries(expensesByCategory).map(
        ([name, value], index) => ({
          name,
          value,
          color: `hsl(${[chart5, chart6, chart7, chart1, chart2, chart3, chart4][index % 7]})`,
        })
      );

      const cashflowData: CashflowData = {
        income: totalIncome,
        expenses: totalExpenses,
        netFlow,
        categories: {
          income: incomeCategories,
          expenses: expenseCategories,
        },
      };

      setCashflowData(cashflowData);
      setIncomeExpenseData(incomeVsExpenses);
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
  }, []);

  // Listen for theme changes
  useEffect(() => {
    const handleThemeChange = () => {
      setThemeKey(prev => prev + 1); // Force re-render with new colors
    };

    // Listen for theme changes by watching for class changes on document
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
    // Get theme-aware colors
    const sankeyNode = getCSSValue('--sankey-node');
    const sankeyText = getCSSValue('--sankey-text');
    const sankeyBg = getCSSValue('--sankey-bg');
    const sankeyBorder = getCSSValue('--sankey-border');

    const nodes = [
      { name: 'Total Income', itemStyle: { color: `hsl(${sankeyNode})` } },
      ...cashflowData.categories.income.map(cat => ({
        name: cat.name,
        itemStyle: { color: cat.color },
      })),
      ...cashflowData.categories.expenses.map(cat => ({
        name: cat.name,
        itemStyle: { color: cat.color },
      })),
      { name: 'Total Expenses', itemStyle: { color: `hsl(${sankeyNode})` } },
    ];

    const links = [
      // Income flows
      ...cashflowData.categories.income.map(cat => ({
        source: 'Total Income',
        target: cat.name,
        value: cat.value,
      })),
      // Expense flows
      ...cashflowData.categories.expenses.map(cat => ({
        source: cat.name,
        target: 'Total Expenses',
        value: cat.value,
      })),
    ];

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
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `${params.data.name}<br/>Value: $${params.data.value?.toLocaleString() || '0'}`;
          } else if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}<br/>Amount: $${params.data.value.toLocaleString()}`;
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
            fontSize: 12,
          },
        },
      ],
    };
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

  // Check if there's no data
  const hasNoData = cashflowData.income === 0 && cashflowData.expenses === 0;

  if (hasNoData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="mb-6">
            <div className="w-20 h-20 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <TrendingUp className="h-10 w-10 text-muted-foreground" />
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              No Cashflow Data
            </h2>
            <p className="text-muted-foreground mb-6">
              No income or expense transactions found. Add some transactions to
              see your cashflow visualization.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Sankey Diagram */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent>
            <div className="h-96">
              <ReactECharts
                key={themeKey} // Force re-render when theme changes
                option={getSankeyOption()}
                style={{ height: '100%', width: '100%' }}
                opts={{ renderer: 'canvas' }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income Categories */}
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-green-600 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Income Sources
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {cashflowData.categories.income.map((category, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: category.color }}
                      />
                      <span className="text-foreground">{category.name}</span>
                    </div>
                    <span className="font-semibold text-foreground">
                      ${category.value.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Expense Categories */}
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-red-600 flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                Expense Categories
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {cashflowData.categories.expenses.map((category, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: category.color }}
                      />
                      <span className="text-foreground">{category.name}</span>
                    </div>
                    <span className="font-semibold text-foreground">
                      ${category.value.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        {/* Income vs Expenses Chart */}
        <div className="lg:col-span-2 min-w-0 overflow-x-auto">
          <IncomeExpenseChart data={incomeExpenseData} />
        </div>
      </div>
    </div>
  );
}
