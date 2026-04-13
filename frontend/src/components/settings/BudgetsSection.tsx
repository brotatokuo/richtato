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
import { PiggyBank, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { BudgetModal } from './BudgetModal';

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

  // Search state
  const [search, setSearch] = useState('');

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] =
    useState<CategoryCatalogItem | null>(null);

  const handleDateChange = (newYear: number, newMonth: number) => {
    setYear(newYear);
    setMonth(newMonth);
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

  // Search filter
  const categoriesWithProgress = allCategoriesWithProgress.filter(cat =>
    search.trim() === '' ||
    cat.display.toLowerCase().includes(search.toLowerCase())
  );

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

  const handleSaveBudget = async (data: {
    amount: number;
    start_date: string;
    end_date: string | null;
  }) => {
    if (!selectedCategory) return;

    await categorySettingsApi.updateSettings({
      enabled: catalog.map(c => c.name),
      disabled: [],
      budgets: {
        [selectedCategory.name]: {
          amount: data.amount,
          start_date: data.start_date,
          end_date: data.end_date,
        },
      },
    });

    // Refresh data
    await fetchData();
  };

  const handleRemoveBudget = async () => {
    if (!selectedCategory) return;

    await categorySettingsApi.updateSettings({
      enabled: catalog.map(c => c.name),
      disabled: [],
      budgets: {
        [selectedCategory.name]: { amount: null },
      },
    });

    // Refresh data
    await fetchData();
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
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
                      {budgetedCategories.length === 1 ? 'category' : 'categories'}{' '}
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
        <CardContent className="space-y-4">
          {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
          {expenseCategories.length === 0 && !loading && (
            <div className="text-sm text-muted-foreground py-4 text-center">
              No expense categories found. Add categories in the Categories tab.
            </div>
          )}
          {expenseCategories.length > 0 && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search categories…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          )}
          {categoriesWithProgress.length === 0 && search.trim() !== '' && (
            <div className="text-sm text-muted-foreground py-2 text-center">
              No categories match &ldquo;{search}&rdquo;
            </div>
          )}
          <div
            className={cn(
              'flex flex-wrap gap-3 transition-opacity',
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
                    'rounded-xl border p-4 w-[180px] cursor-pointer transition-all',
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
