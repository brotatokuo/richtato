interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
  remaining: number;
}

interface CategoryBreakdownProps {
  categories: BudgetCategory[];
}

export function CategoryBreakdown({ categories }: CategoryBreakdownProps) {
  return (
    <div className="h-80 overflow-y-auto">
      <div className="text-sm font-medium text-muted-foreground mb-4">
        Category Breakdown
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {categories.map(category => (
          <div
            key={category.name}
            className="flex items-center justify-between p-3 rounded-lg bg-muted hover:bg-muted/80 transition-colors"
          >
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <div className="relative w-8 h-8 flex-shrink-0">
                {/* Small donut chart */}
                <svg
                  className="w-8 h-8 transform -rotate-90"
                  viewBox="0 0 32 32"
                >
                  <circle
                    cx="16"
                    cy="16"
                    r="12"
                    fill="none"
                    stroke="hsl(var(--muted-foreground) / 0.2)"
                    strokeWidth="4"
                  />
                  <circle
                    cx="16"
                    cy="16"
                    r="12"
                    fill="none"
                    stroke={category.color}
                    strokeWidth="4"
                    strokeDasharray={`${2 * Math.PI * 12}`}
                    strokeDashoffset={`${2 * Math.PI * 12 * (1 - Math.min(category.percentage, 100) / 100)}`}
                    strokeLinecap="round"
                  />
                </svg>
                {/* Center percentage */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-[8px] font-semibold text-foreground">
                    {category.percentage}%
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-foreground truncate">
                  {category.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  ${category.spent.toLocaleString()}/$
                  {category.budget.toLocaleString()}
                </div>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-2">
              <div
                className={`text-xs font-semibold ${
                  category.remaining < 0
                    ? 'text-destructive'
                    : category.percentage > 80
                      ? 'text-yellow-600'
                      : 'text-green-600'
                }`}
              >
                {category.remaining < 0 ? (
                  <span>
                    Over ${Math.abs(category.remaining).toLocaleString()}
                  </span>
                ) : (
                  <span>${category.remaining.toLocaleString()} left</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
