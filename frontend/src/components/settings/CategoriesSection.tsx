import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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
import { useEffect, useRef, useState } from 'react';

interface CategoryGroup {
  type: CategoryType;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  categories: CategoryCatalogItem[];
}

export function CategoriesSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItem[]>([]);
  const [expandedGroups, setExpandedGroups] = useState<Set<CategoryType>>(
    new Set()
  );

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await categorySettingsApi.getCatalog();
        setCatalog(res.categories);
        setError(null);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load categories');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const buildPayload = (
    cat: CategoryCatalogItem[]
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
  const scheduleSave = (next: CategoryCatalogItem[]) => {
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

  const getCategoryType = (cat: CategoryCatalogItem): CategoryType => {
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
            const enabledCount = group.categories.filter(c => c.enabled).length;

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

                      return (
                        <div
                          key={item.name}
                          className={cn(
                            'flex items-center justify-between gap-4 px-4 py-2.5 transition-colors',
                            'hover:bg-muted/30',
                            !item.enabled && 'opacity-50'
                          )}
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
                          <Select
                            value={catType}
                            onValueChange={v =>
                              updateCategoryType(item.name, v as CategoryType)
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

                          {/* Right: Enabled Toggle */}
                          <Switch
                            checked={item.enabled}
                            onCheckedChange={val =>
                              toggleCategory(item.name, Boolean(val))
                            }
                          />
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
  );
}
