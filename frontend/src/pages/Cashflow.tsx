import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import ReactECharts from 'echarts-for-react';
import { DollarSign, TrendingDown, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

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

  // Mock data - replace with actual API call
  useEffect(() => {
    const fetchCashflowData = async () => {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockData: CashflowData = {
        income: 8500,
        expenses: 7200,
        netFlow: 1300,
        categories: {
          income: [
            { name: 'Salary', value: 6000, color: '#10b981' },
            { name: 'Freelance', value: 1500, color: '#059669' },
            { name: 'Investments', value: 800, color: '#047857' },
            { name: 'Other', value: 200, color: '#065f46' },
          ],
          expenses: [
            { name: 'Housing', value: 2500, color: '#ef4444' },
            { name: 'Food', value: 1200, color: '#dc2626' },
            { name: 'Transportation', value: 800, color: '#b91c1c' },
            { name: 'Entertainment', value: 600, color: '#991b1b' },
            { name: 'Utilities', value: 400, color: '#7f1d1d' },
            { name: 'Healthcare', value: 300, color: '#450a0a' },
            { name: 'Savings', value: 1400, color: '#3b82f6' },
          ],
        },
      };

      setCashflowData(mockData);
      setLoading(false);
    };

    fetchCashflowData();
  }, []);

  const getSankeyOption = () => {
    const nodes = [
      { name: 'Total Income', itemStyle: { color: '#10b981' } },
      ...cashflowData.categories.income.map(cat => ({
        name: cat.name,
        itemStyle: { color: cat.color },
      })),
      ...cashflowData.categories.expenses.map(cat => ({
        name: cat.name,
        itemStyle: { color: cat.color },
      })),
      { name: 'Total Expenses', itemStyle: { color: '#ef4444' } },
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
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
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
            borderColor: '#aaa',
          },
          label: {
            color: '#374151',
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
