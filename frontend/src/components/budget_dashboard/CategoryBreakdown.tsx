import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { usePreferences } from '@/contexts/PreferencesContext';
import { formatCurrency, getCurrencySymbol } from '@/lib/format';
import { cn } from '@/lib/utils';
import { Pencil } from 'lucide-react';
import { useEffect, useState } from 'react';

interface BudgetCategory {
  name: string;
  budget: number;
  spent: number;
  percentage: number;
  color: string;
  remaining: number;
}

type SortOption = 'default' | 'over-first' | 'name' | 'spent';

interface CategoryBreakdownProps {
  categories: BudgetCategory[];
  sortBy?: SortOption;
  onEditBudget?: (categoryName: string, newAmount: number) => Promise<void>;
}

function sortCategories(
  categories: BudgetCategory[],
  sortBy: SortOption
): BudgetCategory[] {
  const sorted = [...categories];
  switch (sortBy) {
    case 'over-first':
      return sorted.sort((a, b) => b.percentage - a.percentage);
    case 'name':
      return sorted.sort((a, b) => a.name.localeCompare(b.name));
    case 'spent':
      return sorted.sort((a, b) => b.spent - a.spent);
    default:
      return sorted;
  }
}

function InlineEditPopover({
  category,
  currency,
  onSave,
}: {
  category: BudgetCategory;
  currency: string;
  onSave: (newAmount: number) => Promise<void>;
}) {
  const [amount, setAmount] = useState(String(category.budget));
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const currencySymbol = getCurrencySymbol(currency);

  useEffect(() => {
    if (open) setAmount(String(category.budget));
  }, [open, category.budget]);

  const handleSave = async () => {
    const num = Number(amount);
    if (isNaN(num) || num <= 0) return;
    setSaving(true);
    try {
      await onSave(num);
      setOpen(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="p-1 rounded hover:bg-muted-foreground/10 transition-colors opacity-0 group-hover:opacity-100"
          aria-label={`Edit ${category.name} budget`}
        >
          <Pencil className="h-3 w-3 text-muted-foreground" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-3" align="end">
        <div className="space-y-2">
          <div className="text-sm font-medium">{category.name}</div>
          <div className="relative">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground text-sm select-none">
              {currencySymbol}
            </span>
            <Input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              className="pl-7 h-8 text-sm"
              autoFocus
              onKeyDown={e => {
                if (e.key === 'Enter') handleSave();
                if (e.key === 'Escape') setOpen(false);
              }}
            />
          </div>
          <div className="flex gap-1.5 justify-end">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              className="h-7 text-xs"
              onClick={handleSave}
              disabled={
                saving ||
                !amount ||
                isNaN(Number(amount)) ||
                Number(amount) <= 0
              }
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export function CategoryBreakdown({
  categories,
  sortBy = 'default',
  onEditBudget,
}: CategoryBreakdownProps) {
  const { preferences } = usePreferences();
  const sorted = sortCategories(categories, sortBy);

  return (
    <div className="h-80 overflow-y-auto">
      <div className="text-sm font-medium text-muted-foreground mb-4">
        Category Breakdown
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {sorted.map(category => (
          <div
            key={category.name}
            className="group flex items-center justify-between p-3 rounded-lg bg-muted hover:bg-muted/80 transition-colors"
          >
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <div className="relative w-8 h-8 flex-shrink-0">
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
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-[8px] font-semibold text-foreground">
                    {category.percentage}%
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <div className="text-sm font-medium text-foreground truncate">
                    {category.name}
                  </div>
                  {onEditBudget && (
                    <InlineEditPopover
                      category={category}
                      currency={preferences.currency ?? 'USD'}
                      onSave={newAmount =>
                        onEditBudget(category.name, newAmount)
                      }
                    />
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatCurrency(category.spent, preferences.currency)}/
                  {formatCurrency(category.budget, preferences.currency)}
                </div>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-2">
              <div
                className={cn(
                  'text-xs font-semibold',
                  category.remaining < 0
                    ? 'text-destructive'
                    : category.percentage > 80
                      ? 'text-yellow-600'
                      : 'text-green-600'
                )}
              >
                {category.remaining < 0 ? (
                  <span>
                    Over{' '}
                    {formatCurrency(
                      Math.abs(category.remaining),
                      preferences.currency
                    )}
                  </span>
                ) : (
                  <span>
                    {formatCurrency(category.remaining, preferences.currency)}{' '}
                    left
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
