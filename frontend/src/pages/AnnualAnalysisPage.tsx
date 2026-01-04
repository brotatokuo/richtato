import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  annualAnalysisApiService,
  type AnnualAnalysisData,
} from '@/lib/api/annual-analysis';
import { formatCurrency } from '@/lib/format';
import * as echarts from 'echarts';
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Loader2,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

// Colors for charts
const ESSENTIAL_COLOR = '#22c55e'; // green-500
const NON_ESSENTIAL_COLOR = '#f97316'; // orange-500
const INCOME_COLOR = '#3b82f6'; // blue-500

export function AnnualAnalysisPage() {
  const { preferences } = usePreferences();
  const [data, setData] = useState<AnnualAnalysisData | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number>(
    new Date().getFullYear()
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Chart refs
  const donutChartRef = useRef<HTMLDivElement>(null);
  const barChartRef = useRef<HTMLDivElement>(null);
  const treemapChartRef = useRef<HTMLDivElement>(null);
  const sankeyChartRef = useRef<HTMLDivElement>(null);

  // Chart instances
  const donutChartInstance = useRef<echarts.ECharts | null>(null);
  const barChartInstance = useRef<echarts.ECharts | null>(null);
  const treemapChartInstance = useRef<echarts.ECharts | null>(null);
  const sankeyChartInstance = useRef<echarts.ECharts | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [analysisData, years] = await Promise.all([
        annualAnalysisApiService.getAnnualAnalysis(selectedYear),
        annualAnalysisApiService.getAvailableYears(),
      ]);

      setData(analysisData);
      setAvailableYears(years.length > 0 ? years : [new Date().getFullYear()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [selectedYear]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Initialize and update Donut Chart
  useEffect(() => {
    if (!donutChartRef.current || !data) return;

    if (donutChartInstance.current) {
      donutChartInstance.current.dispose();
    }

    donutChartInstance.current = echarts.init(donutChartRef.current);

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          return `${params.name}: ${formatCurrency(params.value, preferences.currency)} (${params.percent}%)`;
        },
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#9ca3af' },
      },
      series: [
        {
          name: 'Spending',
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#1f2937',
            borderWidth: 2,
          },
          label: {
            show: true,
            position: 'center',
            formatter: () => {
              const total = data.essential_total + data.non_essential_total;
              return `Total\n${formatCurrency(total, preferences.currency)}`;
            },
            fontSize: 14,
            fontWeight: 'bold',
            color: '#f3f4f6',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: [
            {
              value: data.essential_total,
              name: 'Essential',
              itemStyle: { color: ESSENTIAL_COLOR },
            },
            {
              value: data.non_essential_total,
              name: 'Non-Essential',
              itemStyle: { color: NON_ESSENTIAL_COLOR },
            },
          ],
        },
      ],
    };

    donutChartInstance.current.setOption(option);

    return () => {
      donutChartInstance.current?.dispose();
    };
  }, [data, preferences.currency]);

  // Initialize and update Bar Chart
  useEffect(() => {
    if (!barChartRef.current || !data) return;

    if (barChartInstance.current) {
      barChartInstance.current.dispose();
    }

    barChartInstance.current = echarts.init(barChartRef.current);

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const lines = params.map((p: any) => {
            return `<span style="color:${p.color}">●</span> ${p.seriesName}: ${formatCurrency(p.value, preferences.currency)}`;
          });
          return `${params[0].name}<br/>${lines.join('<br/>')}`;
        },
      },
      legend: {
        data: ['Essential', 'Non-Essential'],
        bottom: 0,
        textStyle: { color: '#9ca3af' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.monthly_breakdown.map(m => m.month),
        axisLabel: { color: '#9ca3af' },
        axisLine: { lineStyle: { color: '#374151' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#9ca3af',
          formatter: (value: number) => {
            if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
            return formatCurrency(value, preferences.currency, 0);
          },
        },
        splitLine: { lineStyle: { color: '#374151' } },
      },
      series: [
        {
          name: 'Essential',
          type: 'bar',
          stack: 'total',
          data: data.monthly_breakdown.map(m => m.essential),
          itemStyle: { color: ESSENTIAL_COLOR },
        },
        {
          name: 'Non-Essential',
          type: 'bar',
          stack: 'total',
          data: data.monthly_breakdown.map(m => m.non_essential),
          itemStyle: { color: NON_ESSENTIAL_COLOR },
        },
      ],
    };

    barChartInstance.current.setOption(option);

    return () => {
      barChartInstance.current?.dispose();
    };
  }, [data, preferences.currency]);

  // Initialize and update Treemap Chart
  useEffect(() => {
    if (!treemapChartRef.current || !data) return;

    if (treemapChartInstance.current) {
      treemapChartInstance.current.dispose();
    }

    treemapChartInstance.current = echarts.init(treemapChartRef.current);

    // Group categories by essential/non-essential
    const essentialCategories = data.category_breakdown
      .filter(c => c.is_essential)
      .map(c => ({
        name: c.name,
        value: c.amount,
        itemStyle: { color: c.color || ESSENTIAL_COLOR },
      }));

    const nonEssentialCategories = data.category_breakdown
      .filter(c => !c.is_essential)
      .map(c => ({
        name: c.name,
        value: c.amount,
        itemStyle: { color: c.color || NON_ESSENTIAL_COLOR },
      }));

    const option: echarts.EChartsOption = {
      tooltip: {
        formatter: (params: any) => {
          return `${params.name}: ${formatCurrency(params.value, preferences.currency)}`;
        },
      },
      series: [
        {
          type: 'treemap',
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          levels: [
            {
              itemStyle: {
                borderColor: '#1f2937',
                borderWidth: 2,
                gapWidth: 2,
              },
            },
            {
              itemStyle: {
                borderColor: '#374151',
                borderWidth: 1,
                gapWidth: 1,
              },
              upperLabel: {
                show: true,
                height: 24,
                color: '#f3f4f6',
                backgroundColor: 'transparent',
              },
            },
          ],
          data: [
            {
              name: 'Essential',
              itemStyle: { color: ESSENTIAL_COLOR, borderColor: ESSENTIAL_COLOR },
              children: essentialCategories,
            },
            {
              name: 'Non-Essential',
              itemStyle: {
                color: NON_ESSENTIAL_COLOR,
                borderColor: NON_ESSENTIAL_COLOR,
              },
              children: nonEssentialCategories,
            },
          ],
          label: {
            show: true,
            formatter: '{b}',
            color: '#fff',
            fontSize: 11,
          },
        },
      ],
    };

    treemapChartInstance.current.setOption(option);

    return () => {
      treemapChartInstance.current?.dispose();
    };
  }, [data, preferences.currency]);

  // Initialize and update Sankey Chart
  useEffect(() => {
    if (!sankeyChartRef.current || !data) return;

    if (sankeyChartInstance.current) {
      sankeyChartInstance.current.dispose();
    }

    sankeyChartInstance.current = echarts.init(sankeyChartRef.current);

    // Build nodes and links for Sankey
    const nodes: { name: string; itemStyle?: { color: string } }[] = [];
    const links: { source: string; target: string; value: number }[] = [];

    // Add income sources as nodes
    data.income_sources.forEach(source => {
      nodes.push({
        name: source.name,
        itemStyle: { color: source.color || INCOME_COLOR },
      });
    });

    // Add "Total Income" node
    nodes.push({ name: 'Total Income', itemStyle: { color: INCOME_COLOR } });

    // Add Essential/Non-Essential nodes
    nodes.push({ name: 'Essential', itemStyle: { color: ESSENTIAL_COLOR } });
    nodes.push({
      name: 'Non-Essential',
      itemStyle: { color: NON_ESSENTIAL_COLOR },
    });

    // Add expense category nodes
    data.category_breakdown.forEach(cat => {
      nodes.push({
        name: cat.name,
        itemStyle: { color: cat.color || '#6b7280' },
      });
    });

    // Add Savings node if income > expenses
    const totalExpenses = data.essential_total + data.non_essential_total;
    if (data.total_income > totalExpenses) {
      nodes.push({ name: 'Savings', itemStyle: { color: '#10b981' } });
    }

    // Links: Income sources -> Total Income
    data.income_sources.forEach(source => {
      links.push({
        source: source.name,
        target: 'Total Income',
        value: source.amount,
      });
    });

    // Links: Total Income -> Essential/Non-Essential
    links.push({
      source: 'Total Income',
      target: 'Essential',
      value: data.essential_total,
    });
    links.push({
      source: 'Total Income',
      target: 'Non-Essential',
      value: data.non_essential_total,
    });

    // Link to Savings if applicable
    if (data.total_income > totalExpenses) {
      links.push({
        source: 'Total Income',
        target: 'Savings',
        value: data.total_income - totalExpenses,
      });
    }

    // Links: Essential/Non-Essential -> Categories
    data.category_breakdown.forEach(cat => {
      links.push({
        source: cat.is_essential ? 'Essential' : 'Non-Essential',
        target: cat.name,
        value: cat.amount,
      });
    });

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        formatter: (params: any) => {
          if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}<br/>${formatCurrency(params.data.value, preferences.currency)}`;
          }
          return params.name;
        },
      },
      series: [
        {
          type: 'sankey',
          layout: 'none',
          emphasis: {
            focus: 'adjacency',
          },
          nodeAlign: 'left',
          data: nodes,
          links: links,
          lineStyle: {
            color: 'gradient',
            curveness: 0.5,
          },
          label: {
            color: '#f3f4f6',
            fontSize: 11,
          },
        },
      ],
    };

    sankeyChartInstance.current.setOption(option);

    return () => {
      sankeyChartInstance.current?.dispose();
    };
  }, [data, preferences.currency]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      donutChartInstance.current?.resize();
      barChartInstance.current?.resize();
      treemapChartInstance.current?.resize();
      sankeyChartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
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

  const totalExpenses = data.essential_total + data.non_essential_total;
  const essentialPercent =
    totalExpenses > 0
      ? Math.round((data.essential_total / totalExpenses) * 100)
      : 0;
  const savingsAmount = data.total_income - totalExpenses;
  const savingsRate =
    data.total_income > 0
      ? Math.round((savingsAmount / data.total_income) * 100)
      : 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header with Year Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Annual Analysis</h1>
          <p className="text-sm text-muted-foreground">
            Comprehensive spending breakdown for {selectedYear}
          </p>
        </div>
        <Select
          value={String(selectedYear)}
          onValueChange={value => setSelectedYear(Number(value))}
        >
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Year" />
          </SelectTrigger>
          <SelectContent>
            {availableYears.map(year => (
              <SelectItem key={year} value={String(year)}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Income</p>
                <p className="text-2xl font-bold text-green-500">
                  {formatCurrency(data.total_income, preferences.currency)}
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
                <p className="text-sm text-muted-foreground">Total Expenses</p>
                <p className="text-2xl font-bold text-orange-500">
                  {formatCurrency(totalExpenses, preferences.currency)}
                </p>
              </div>
              <ArrowDownRight className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Essential %</p>
                <p className="text-2xl font-bold text-foreground">
                  {essentialPercent}%
                </p>
              </div>
              <Wallet className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Savings Rate</p>
                <p
                  className={`text-2xl font-bold ${savingsAmount >= 0 ? 'text-green-500' : 'text-red-500'}`}
                >
                  {savingsRate}%
                </p>
              </div>
              <TrendingUp
                className={`h-8 w-8 ${savingsAmount >= 0 ? 'text-green-500' : 'text-red-500'}`}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Essential vs Non-Essential Donut */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">
              Essential vs Non-Essential
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div ref={donutChartRef} className="h-80" />
          </CardContent>
        </Card>

        {/* Monthly Spending Trends */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Monthly Spending Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div ref={barChartRef} className="h-80" />
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Category Treemap */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Category Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div ref={treemapChartRef} className="h-80" />
          </CardContent>
        </Card>

        {/* Income Flow Sankey */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Income Flow</CardTitle>
          </CardHeader>
          <CardContent>
            <div ref={sankeyChartRef} className="h-80" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
