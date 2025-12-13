import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  CategoryCatalogItem,
  CategorySettingsPayload,
  CategoryType,
  categorySettingsApi,
} from '@/lib/api/user';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Tags } from 'lucide-react';
import { FormEvent, useEffect, useRef, useState } from 'react';

type CategoryCatalogItemWithId = CategoryCatalogItem & { id: number };

interface CategoryGroup {
  type: CategoryType;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  categories: CategoryCatalogItemWithId[];
}

export function CategoriesSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItemWithId[]>([]);
  const [keywordRules, setKeywordRules] = useState<
    Array<{
      id: number;
      keyword: string;
      category: number;
      category_name: string;
    }>
  >([]);
  const [expandedGroups, setExpandedGroups] = useState<Set<CategoryType>>(
    new Set()
  );
  const [dialogOpen, setDialogOpen] = useState(false);
  const [keywordValue, setKeywordValue] = useState('');
  const [selectedCategory, setSelectedCategory] =
    useState<CategoryCatalogItemWithId | null>(null);
  const [savingKeyword, setSavingKeyword] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [catalogRes, rulesRes] = await Promise.all([
          categorySettingsApi.getCatalog(),
          categorySettingsApi.listKeywordRules(),
        ]);
        setCatalog(catalogRes.categories as CategoryCatalogItemWithId[]);
        setKeywordRules(rulesRes.rules || []);
        setError(null);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load categories');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const buildPayload = (
    cat: CategoryCatalogItemWithId[]
  ): CategorySettingsPayload => {
    const enabled = cat.filter(c => c.enabled).map(c => c.name);
    const disabled = cat.filter(c => !c.enabled).map(c => c.name);
    const category_types: Record<string, CategoryType> = {};
    for (const c of cat) {
      if (c.is_income) {
        category_types[c.name] = 'income';
      } else if (c.is_expense) {
        category_types[c.name] = 'expense';
      } else {
        category_types[c.name] = 'neither';
      }
    }
    return { enabled, disabled, category_types };
  };

  const saveTimer = useRef<number | undefined>(undefined);
  const scheduleSave = (next: CategoryCatalogItemWithId[]) => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(async () => {
      try {
        const p = buildPayload(next);
        await categorySettingsApi.updateSettings(p);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to auto-save');
      }
    }, 500);
  };

  const toggleCategory = (name: string, value: boolean) => {
    setCatalog(prev => {
      const next = prev.map(c =>
        c.name === name ? { ...c, enabled: value } : c
      );
      scheduleSave(next);
      return next;
    });
  };

  const updateCategoryType = (name: string, type: CategoryType) => {
    setCatalog(prev => {
      const next = prev.map(c => {
        if (c.name !== name) return c;
        return {
          ...c,
          is_income: type === 'income',
          is_expense: type === 'expense',
        };
      });
      scheduleSave(next);
      return next;
    });
  };

  const getCategoryType = (cat: CategoryCatalogItemWithId): CategoryType => {
    if (cat.is_income) return 'income';
    if (cat.is_expense) return 'expense';
    return 'neither';
  };

  const toggleGroup = (type: CategoryType) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const openKeywordDialog = (category: CategoryCatalogItemWithId) => {
    setSelectedCategory(category);
    setKeywordValue('');
    setDialogOpen(true);
  };

  const closeKeywordDialog = () => {
    if (savingKeyword) return;
    setDialogOpen(false);
    setSelectedCategory(null);
    setKeywordValue('');
  };

  const handleSubmitKeyword = async (e?: FormEvent) => {
    e?.preventDefault();
    const keyword = keywordValue.trim();
    if (!keyword || !selectedCategory) return;
    setSavingKeyword(true);
    try {
      const rule = await categorySettingsApi.createKeywordRule({
        keyword,
        category: selectedCategory.id,
      });
      setKeywordRules(prev => [...prev, rule]);
      setDialogOpen(false);
      setSelectedCategory(null);
      setKeywordValue('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to add keyword');
    } finally {
      setSavingKeyword(false);
    }
  };

  const handleDeleteKeyword = async (id: number) => {
    try {
      await categorySettingsApi.deleteKeywordRule(id);
      setKeywordRules(prev => prev.filter(r => r.id !== id));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete keyword');
    }
  };

  // Group categories by type
  const allGroups: CategoryGroup[] = [
    {
      type: 'expense' as CategoryType,
      label: 'Expenses',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-50 dark:bg-orange-950/30',
      categories: catalog.filter(c => c.is_expense),
    },
    {
      type: 'income' as CategoryType,
      label: 'Income',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />,
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
      categories: catalog.filter(c => c.is_income),
    },
    {
      type: 'neither' as CategoryType,
      label: 'Other',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-gray-400" />,
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-50 dark:bg-gray-900/30',
      categories: catalog.filter(c => !c.is_income && !c.is_expense),
    },
  ];
  const groups = allGroups.filter(g => g.categories.length > 0);

  return (
    <>
      <Dialog
        open={dialogOpen}
        onOpenChange={open => {
          if (!open) closeKeywordDialog();
          else setDialogOpen(true);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add keyword</DialogTitle>
            <DialogDescription>
              Map transactions containing this keyword to the selected category.
            </DialogDescription>
          </DialogHeader>

          <form className="space-y-4" onSubmit={handleSubmitKeyword}>
            <div className="space-y-1">
              <div className="text-sm font-semibold">
                {selectedCategory?.display ?? 'Select a category'}
              </div>
              <div className="text-xs text-muted-foreground">
                Keywords are matched case-insensitively against transaction
                descriptions.
              </div>
            </div>

            <Input
              autoFocus
              placeholder="Keyword (e.g., uber, netflix)"
              value={keywordValue}
              onChange={e => setKeywordValue(e.target.value)}
              disabled={savingKeyword}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={closeKeywordDialog}
                disabled={savingKeyword}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!keywordValue.trim() || savingKeyword}
              >
                {savingKeyword ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tags className="h-5 w-5" />
            Categories
          </CardTitle>
          <CardDescription>
            Manage your transaction categories and types
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
          {loading && <div className="text-sm">Loading...</div>}
          {!loading && catalog.length === 0 && (
            <div className="text-sm text-muted-foreground py-4 text-center">
              No categories found
            </div>
          )}
          {!loading &&
            groups.map(group => {
              const isExpanded = expandedGroups.has(group.type);
              const enabledCount = group.categories.filter(
                c => c.enabled
              ).length;

              return (
                <div
                  key={group.type}
                  className="border rounded-lg overflow-hidden"
                >
                  {/* Group Header */}
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.type)}
                    className={cn(
                      'w-full flex items-center justify-between px-4 py-3 transition-colors',
                      'hover:bg-muted/50',
                      group.bgColor
                    )}
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                      {group.icon}
                      <span className={cn('font-semibold', group.color)}>
                        {group.label}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {enabledCount} / {group.categories.length} enabled
                    </span>
                  </button>

                  {/* Group Content */}
                  {isExpanded && (
                    <div className="divide-y">
                      {group.categories.map(item => {
                        const catType = getCategoryType(item);
                        const rulesForCategory = keywordRules.filter(
                          r => r.category === item.id
                        );

                        return (
                          <div key={item.name} className="divide-y">
                            <div
                              className={cn(
                                'flex items-center justify-between gap-4 px-4 py-2.5 transition-colors cursor-pointer',
                                'hover:bg-muted/30',
                                !item.enabled && 'opacity-50'
                              )}
                              onClick={() => openKeywordDialog(item)}
                              title="Click to add a keyword rule for this category"
                            >
                              {/* Left: Icon + Name */}
                              <div className="flex items-center gap-3 min-w-0 flex-1">
                                <span className="text-lg" aria-hidden>
                                  {item.icon}
                                </span>
                                <span className="font-medium truncate text-sm">
                                  {item.display}
                                </span>
                              </div>

                              {/* Center: Type Selector */}
                              <div onClick={e => e.stopPropagation()}>
                                <Select
                                  value={catType}
                                  onValueChange={v =>
                                    updateCategoryType(
                                      item.name,
                                      v as CategoryType
                                    )
                                  }
                                >
                                  <SelectTrigger className="w-[100px] h-7 text-xs">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="expense">
                                      <span className="flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-orange-500" />
                                        Expense
                                      </span>
                                    </SelectItem>
                                    <SelectItem value="income">
                                      <span className="flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                        Income
                                      </span>
                                    </SelectItem>
                                    <SelectItem value="neither">
                                      <span className="flex items-center gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-gray-400" />
                                        Other
                                      </span>
                                    </SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>

                              {/* Right: Enabled Toggle */}
                              <div onClick={e => e.stopPropagation()}>
                                <Switch
                                  checked={item.enabled}
                                  onCheckedChange={val =>
                                    toggleCategory(item.name, Boolean(val))
                                  }
                                />
                              </div>
                            </div>

                            {rulesForCategory.length > 0 && (
                              <div className="space-y-1 px-8 py-2 text-xs bg-muted/20">
                                {rulesForCategory.map(rule => (
                                  <div
                                    key={rule.id}
                                    className="flex items-center justify-between rounded border px-2 py-1 bg-background"
                                  >
                                    <span className="font-mono text-[11px]">
                                      {rule.keyword}
                                    </span>
                                    <button
                                      type="button"
                                      className="text-[11px] text-red-500 hover:underline"
                                      onClick={e => {
                                        e.stopPropagation();
                                        handleDeleteKeyword(rule.id);
                                      }}
                                    >
                                      Remove
                                    </button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
        </CardContent>
      </Card>
    </>
  );
}
