import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import ReactECharts from 'echarts-for-react';
import { TrendingDown, TrendingUp } from 'lucide-react';
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
  const [themeKey, setThemeKey] = useState(0); // Force re-render when theme changes

  // Mock data - replace with actual API call
  useEffect(() => {
    const fetchCashflowData = async () => {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Get theme-aware colors
      const chart1 = getCSSValue('--chart-1');
      const chart2 = getCSSValue('--chart-2');
      const chart3 = getCSSValue('--chart-3');
      const chart4 = getCSSValue('--chart-4');
      const chart5 = getCSSValue('--chart-5');
      const chart6 = getCSSValue('--chart-6');
      const chart7 = getCSSValue('--chart-7');

      const mockData: CashflowData = {
        income: 8500,
        expenses: 7200,
        netFlow: 1300,
        categories: {
          income: [
            { name: 'Salary', value: 6000, color: `hsl(${chart1})` },
            { name: 'Freelance', value: 1500, color: `hsl(${chart2})` },
            { name: 'Investments', value: 800, color: `hsl(${chart3})` },
            { name: 'Other', value: 200, color: `hsl(${chart4})` },
          ],
          expenses: [
            { name: 'Housing', value: 2500, color: `hsl(${chart5})` },
            { name: 'Food', value: 1200, color: `hsl(${chart6})` },
            { name: 'Transportation', value: 800, color: `hsl(${chart7})` },
            { name: 'Entertainment', value: 600, color: `hsl(${chart1})` },
            { name: 'Utilities', value: 400, color: `hsl(${chart2})` },
            { name: 'Healthcare', value: 300, color: `hsl(${chart3})` },
            { name: 'Savings', value: 1400, color: `hsl(${chart4})` },
          ],
        },
      };

      setCashflowData(mockData);
      setLoading(false);
    };

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
    const sankeyLink = getCSSValue('--sankey-link');
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading cashflow data...</p>
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
      </div>
    </div>
  );
}
