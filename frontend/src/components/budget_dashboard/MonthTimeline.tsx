import { usePreferences } from '@/contexts/PreferencesContext';
import type { MonthlyBudgetData } from '@/lib/api/budget-dashboard';
import { formatCurrency } from '@/lib/format';
import { TrendingDown, TrendingUp } from 'lucide-react';

interface MonthTimelineProps {
  monthlyData: MonthlyBudgetData[];
  onMonthClick: (month: MonthlyBudgetData) => void;
  loading?: boolean;
  selectedYear?: number;
  selectedMonth?: number;
}

export function MonthTimeline({
  monthlyData,
  onMonthClick,
  loading,
  selectedYear,
  selectedMonth: selectedMonthProp,
}: MonthTimelineProps) {
  const { preferences } = usePreferences();
  // Determine current month
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  if (loading) {
    return (
      <div className="relative">
        <div className="flex gap-4 overflow-x-hidden py-2">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="flex-shrink-0 w-64 h-40 bg-muted/50 rounded-xl animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (!monthlyData || monthlyData.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No budget data available
      </div>
    );
  }

  return (
    <div className="w-full min-w-0">
      {/* Timeline Grid (no horizontal scroll) */}
      <div className="grid gap-3 py-2 px-1 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {monthlyData.map(month => {
          const isCurrentMonth =
            month.year === currentYear && month.month === currentMonth;
          const isSelected =
            selectedYear !== undefined &&
            selectedMonthProp !== undefined &&
            month.year === selectedYear &&
            month.month === selectedMonthProp;
          const isOverBudget = month.percentage > 100;
          const isWarning = month.percentage > 80 && !isOverBudget;

          return (
            <button
              key={`${month.year}-${month.month}`}
              onClick={() => onMonthClick(month)}
              className={`w-full p-3 rounded-xl border transition-all duration-200 hover:shadow-lg cursor-pointer text-left ${
                isSelected
                  ? 'border-primary bg-primary/10 ring-2 ring-primary shadow-md'
                  : isCurrentMonth
                    ? 'border-primary/50 bg-primary/5'
                    : 'border-border bg-card hover:border-primary/50'
              }`}
            >
              {/* Month Header */}
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-base font-semibold text-foreground">
                    {month.month_name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {month.year}
                  </div>
                </div>
                <div className="flex gap-1">
                  {isSelected && (
                    <span className="text-xs font-medium bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
                      Viewing
                    </span>
                  )}
                  {isCurrentMonth && !isSelected && (
                    <span className="text-xs font-medium bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                      Current
                    </span>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full transition-all duration-500 ${
                    isOverBudget
                      ? 'bg-red-500'
                      : isWarning
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(month.percentage, 100)}%` }}
                />
              </div>

              {/* Stats */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Spent</span>
                  <span
                    className={`font-medium ${isOverBudget ? 'text-red-500' : 'text-foreground'}`}
                  >
                    {formatCurrency(
                      month.total_spent,
                      preferences.currency ?? 'USD'
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Budget</span>
                  <span className="font-medium text-foreground">
                    {formatCurrency(
                      month.total_budget,
                      preferences.currency ?? 'USD'
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-xs pt-1 border-t border-border/50">
                  <span className="text-muted-foreground">
                    {isOverBudget ? 'Over' : 'Left'}
                  </span>
                  <span
                    className={`font-semibold flex items-center gap-0.5 ${
                      isOverBudget ? 'text-red-500' : 'text-emerald-500'
                    }`}
                  >
                    {isOverBudget ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {formatCurrency(
                      Math.abs(month.total_remaining),
                      preferences.currency ?? 'USD'
                    )}
                  </span>
                </div>
              </div>

              {/* Usage Percentage Badge */}
              <div className="mt-2 text-center">
                <span
                  className={`inline-block text-xs font-bold px-2 py-0.5 rounded-full ${
                    isOverBudget
                      ? 'bg-red-500/20 text-red-500'
                      : isWarning
                        ? 'bg-amber-500/20 text-amber-600'
                        : 'bg-emerald-500/20 text-emerald-600'
                  }`}
                >
                  {month.percentage}% used
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
