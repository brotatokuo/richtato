import { usePreferences } from '@/contexts/PreferencesContext';
import type { MonthlyBudgetData } from '@/lib/api/budget-dashboard';
import { formatCurrency } from '@/lib/format';
import {
  ChevronLeft,
  ChevronRight,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

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
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = () => {
    const container = scrollContainerRef.current;
    if (container) {
      setCanScrollLeft(container.scrollLeft > 0);
      setCanScrollRight(
        container.scrollLeft <
          container.scrollWidth - container.clientWidth - 10
      );
    }
  };

  useEffect(() => {
    checkScroll();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScroll);
      window.addEventListener('resize', checkScroll);
    }
    return () => {
      if (container) {
        container.removeEventListener('scroll', checkScroll);
      }
      window.removeEventListener('resize', checkScroll);
    };
  }, [monthlyData]);

  // Scroll to the current month (last item) on initial load
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container && monthlyData.length > 0) {
      // Scroll to end to show current month
      setTimeout(() => {
        container.scrollTo({
          left: container.scrollWidth,
          behavior: 'smooth',
        });
      }, 100);
    }
  }, [monthlyData.length]);

  const scroll = (direction: 'left' | 'right') => {
    const container = scrollContainerRef.current;
    if (container) {
      const scrollAmount = 280; // Approximate width of a card + gap
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

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
    <div className="relative group w-full">
      {/* Left Scroll Button */}
      {canScrollLeft && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-background/90 backdrop-blur-sm border border-border rounded-full p-2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted"
          aria-label="Scroll left"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
      )}

      {/* Right Scroll Button */}
      {canScrollRight && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-background/90 backdrop-blur-sm border border-border rounded-full p-2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted"
          aria-label="Scroll right"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      )}

      {/* Timeline Container */}
      <div
        ref={scrollContainerRef}
        className="flex gap-3 py-2 px-1 overflow-x-auto scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent"
        style={{ scrollbarWidth: 'thin' }}
      >
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
              className={`flex-shrink-0 w-56 p-3 rounded-xl border transition-all duration-200 hover:scale-[1.02] hover:shadow-lg cursor-pointer text-left ${
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
