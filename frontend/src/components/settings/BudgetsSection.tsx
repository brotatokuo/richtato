import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import { usePreferences } from '@/contexts/PreferencesContext';
import { transactionsApiService } from '@/lib/api/transactions';
import { CategoryCatalogItem, categorySettingsApi } from '@/lib/api/user';
import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';
import { ArrowUpDown, PiggyBank, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { BudgetModal } from './BudgetModal';

type SortOption = 'default' | 'budgeted-first' | 'name' | 'spent';

interface BudgetProgress {
  category: string;
  budget: number;
  spent: number;
  percentage: number;
  remaining: number;
}

export function BudgetsSection() {
  const { preferences } = usePreferences();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItem[]>([]);
  const [progress, setProgress] = useState<BudgetProgress[]>([]);
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [month, setMonth] = useState(() => new Date().getMonth() + 1);

  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('default');

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] =
    useState<CategoryCatalogItem | null>(null);

  const handleDateChange = (newYear: number, newMonth: number) => {
    setYear(newYear);
    setMonth(newMonth);
  };

  const selectedPeriod = () => {
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0);
    const toDateString = (date: Date) =>
      [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, '0'),
        String(date.getDate()).padStart(2, '0'),
      ].join('-');
    return {
      start_date: toDateString(startDate),
      end_date: toDateString(endDate),
    };
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch catalog and budget progress in parallel
      const [catalogRes, progressRes] = await Promise.all([
        categorySettingsApi.getCatalog(),
        transactionsApiService.getBudgetDashboard({ year, month }),
      ]);

      setCatalog(catalogRes.categories);
      setProgress(progressRes.budgets || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load budget data');
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter to only show expense categories
  const expenseCategories = catalog.filter(c => c.type === 'expense');

  // Merge budget data with progress
  const allCategoriesWithProgress = expenseCategories.map(cat => {
    const prog = progress.find(
      p =>
        p.category.toLowerCase().replace(/\s+/g, '-') === cat.name ||
        p.category === cat.display
    );
    return {
      ...cat,
      spent: prog?.spent ?? 0,
      percentage: prog?.percentage ?? 0,
      remaining: prog?.remaining ?? cat.budget?.amount ?? 0,
    };
  });

  const filteredCategories = allCategoriesWithProgress.filter(
    cat =>
      search.trim() === '' ||
      cat.display.toLowerCase().includes(search.toLowerCase())
  );

  const categoriesWithProgress = [...filteredCategories].sort((a, b) => {
    switch (sortBy) {
      case 'budgeted-first': {
        const aHas = a.budget != null && a.budget.amount > 0 ? 1 : 0;
        const bHas = b.budget != null && b.budget.amount > 0 ? 1 : 0;
        return bHas - aHas;
      }
      case 'name':
        return a.display.localeCompare(b.display);
      case 'spent':
        return b.spent - a.spent;
      default:
        return 0;
    }
  });

  // Total monthly budget summary
  const budgetedCategories = allCategoriesWithProgress.filter(
    c => c.budget != null && c.budget.amount > 0
  );
  const totalBudget = budgetedCategories.reduce(
    (sum, c) => sum + (c.budget?.amount ?? 0),
    0
  );

  const openModal = (cat: CategoryCatalogItem) => {
    setSelectedCategory(cat);
    setModalOpen(true);
  };

  const handleSaveBudget = async (data: { amount: number }) => {
    if (!selectedCategory) return;

    await categorySettingsApi.updateSettings({
      budgets: {
        [selectedCategory.name]: { amount: data.amount, ...selectedPeriod() },
      },
    });

    await fetchData();
  };

  const handleRemoveBudget = async () => {
    if (!selectedCategory) return;

    await categorySettingsApi.updateSettings({
      budgets: {
        [selectedCategory.name]: { amount: null, ...selectedPeriod() },
      },
    });

    // Refresh data
    await fetchData();
  };

  return (
    <>
      <Card className="overflow-hidden">
        <CardHeader className="p-4 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <CardTitle className="flex items-center gap-2 text-xl sm:text-2xl">
                <PiggyBank className="h-5 w-5" />
                Monthly Budgets
              </CardTitle>
              <CardDescription className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-0.5">
                <span>Set spending limits per category</span>
                {budgetedCategories.length > 0 && (
                  <>
                    <span className="text-muted-foreground/40">·</span>
                    <span>
                      {budgetedCategories.length}{' '}
                      {budgetedCategories.length === 1
                        ? 'category'
                        : 'categories'}{' '}
                      &middot;{' '}
                      <span className="font-medium text-foreground">
                        {formatCurrency(totalBudget, preferences.currency)}/mo
                      </span>{' '}
                      budgeted
                    </span>
                  </>
                )}
              </CardDescription>
            </div>
            <MonthYearPicker
              year={year}
              month={month}
              onChange={handleDateChange}
              className="static"
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-4 p-4 pt-0 sm:p-6 sm:pt-0">
          {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
          {expenseCategories.length === 0 && !loading && (
            <div className="text-sm text-muted-foreground py-4 text-center">
              No expense categories found. Add categories in the Categories tab.
            </div>
          )}
          {expenseCategories.length > 0 && (
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  placeholder="Search categories…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="relative sm:w-auto">
                <select
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as SortOption)}
                  className="h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 pr-7 text-sm text-muted-foreground transition-colors hover:text-foreground sm:w-auto"
                >
                  <option value="default">Default</option>
                  <option value="budgeted-first">Budgeted first</option>
                  <option value="name">Name A-Z</option>
                  <option value="spent">Most spent</option>
                </select>
                <ArrowUpDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground pointer-events-none" />
              </div>
            </div>
          )}
          {categoriesWithProgress.length === 0 && search.trim() !== '' && (
            <div className="text-sm text-muted-foreground py-2 text-center">
              No categories match &ldquo;{search}&rdquo;
            </div>
          )}
          <div
            className={cn(
              'grid grid-cols-1 gap-3 transition-opacity sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
              loading && 'opacity-50 pointer-events-none'
            )}
          >
            {categoriesWithProgress.map(cat => {
              const hasBudget = cat.budget != null && cat.budget.amount > 0;
              const budgetAmount = cat.budget?.amount ?? 0;
              const isOverBudget = hasBudget && cat.spent > budgetAmount;
              const progressPercent = hasBudget
                ? Math.min((cat.spent / budgetAmount) * 100, 100)
                : 0;

              return (
                <div
                  key={cat.name}
                  onClick={() => openModal(cat)}
                  className={cn(
                    'min-w-0 cursor-pointer rounded-xl border p-4 transition-all',
                    'hover:shadow-md hover:border-primary/40 hover:-translate-y-0.5',
                    isOverBudget
                      ? 'border-destructive/50 bg-destructive/5'
                      : 'bg-card'
                  )}
                >
                  {/* Header: Icon + Name */}
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl" aria-hidden>
                      {cat.icon}
                    </span>
                    <span className="font-medium text-sm truncate flex-1">
                      {cat.display}
                    </span>
                  </div>

                  {/* Budget Amount */}
                  <div className="mb-2">
                    {hasBudget ? (
                      <div className="text-lg font-semibold">
                        {formatCurrency(budgetAmount, preferences.currency)}
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground italic">
                        No budget
                      </div>
                    )}
                  </div>

                  {/* Progress Section */}
                  {hasBudget ? (
                    <>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-2">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all duration-300',
                            isOverBudget
                              ? 'bg-destructive'
                              : progressPercent > 80
                                ? 'bg-amber-500'
                                : 'bg-primary'
                          )}
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span
                          className={cn(
                            isOverBudget && 'text-destructive font-medium'
                          )}
                        >
                          {formatCurrency(cat.spent, preferences.currency)}
                        </span>
                        <span>
                          {Math.round(cat.percentage || progressPercent)}%
                        </span>
                      </div>
                    </>
                  ) : null}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <BudgetModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedCategory(null);
        }}
        onSave={handleSaveBudget}
        onRemove={handleRemoveBudget}
        category={selectedCategory}
        loading={loading}
      />
    </>
  );
}
