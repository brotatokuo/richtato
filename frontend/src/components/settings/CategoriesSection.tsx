import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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
import { ChevronDown, ChevronRight, Search, Tags } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { BulkKeywordsModal } from './BulkKeywordsModal';

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
  const [expandedGroups, setExpandedGroups] = useState<Set<CategoryType>>(
    new Set()
  );
  const [keywordModalOpen, setKeywordModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] =
    useState<CategoryCatalogItemWithId | null>(null);
  const [globalKeywordSearch, setGlobalKeywordSearch] = useState('');

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    try {
      setLoading(true);
      const catalogRes = await categorySettingsApi.getCatalog();
      setCatalog(catalogRes.categories as CategoryCatalogItemWithId[]);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  const buildPayload = (
    cat: CategoryCatalogItemWithId[]
  ): CategorySettingsPayload => {
    const enabled = cat.filter(c => c.enabled).map(c => c.name);
    const disabled = cat.filter(c => !c.enabled).map(c => c.name);
    const category_types: Record<string, CategoryType> = {};
    for (const c of cat) {
      // Use type field if available, fallback to expense for backward compatibility
      const catType = c.type || 'expense';
      category_types[c.name] = catType as CategoryType;
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
          type: type,
        };
      });
      scheduleSave(next);
      return next;
    });
  };

  const getCategoryType = (cat: CategoryCatalogItemWithId): CategoryType => {
    // Use type field if available, fallback to expense for backward compatibility
    return (cat.type as CategoryType) || 'expense';
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

  const openKeywordModal = (category: CategoryCatalogItemWithId) => {
    setSelectedCategory(category);
    setKeywordModalOpen(true);
  };

  const closeKeywordModal = () => {
    setKeywordModalOpen(false);
    setSelectedCategory(null);
  };

  const handleKeywordsChanged = () => {
    // Reload catalog to get updated keyword counts
    loadCatalog();
  };

  // Group categories by type
  // Default to 'expense' if type is null (for backward compatibility)
  const allGroups: CategoryGroup[] = [
    {
      type: 'expense' as CategoryType,
      label: 'Expenses',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-50 dark:bg-orange-950/30',
      categories: catalog.filter(
        c => c.type === 'expense' || c.type === null || c.type === undefined
      ),
    },
    {
      type: 'income' as CategoryType,
      label: 'Income',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />,
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
      categories: catalog.filter(c => c.type === 'income'),
    },
    {
      type: 'transfer' as CategoryType,
      label: 'Transfers',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-950/30',
      categories: catalog.filter(c => c.type === 'transfer'),
    },
    {
      type: 'investment' as CategoryType,
      label: 'Investments',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-950/30',
      categories: catalog.filter(c => c.type === 'investment'),
    },
    {
      type: 'other' as CategoryType,
      label: 'Other',
      icon: <span className="w-2.5 h-2.5 rounded-full bg-gray-500" />,
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-50 dark:bg-gray-950/30',
      categories: catalog.filter(c => c.type === 'other'),
    },
  ];

  // Filter groups based on global keyword search
  const filteredGroups = globalKeywordSearch
    ? allGroups
        .map(group => ({
          ...group,
          categories: group.categories.filter(cat => {
            if (!cat.keywords) return false;
            return cat.keywords.some(kw =>
              kw.keyword
                .toLowerCase()
                .includes(globalKeywordSearch.toLowerCase())
            );
          }),
        }))
        .filter(g => g.categories.length > 0)
    : allGroups.filter(g => g.categories.length > 0);

  return (
    <>
      {selectedCategory && (
        <BulkKeywordsModal
          open={keywordModalOpen}
          onClose={closeKeywordModal}
          categoryId={selectedCategory.id}
          categoryName={selectedCategory.display}
          categoryIcon={selectedCategory.icon}
          onKeywordsChanged={handleKeywordsChanged}
        />
      )}

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
        <CardContent className="space-y-4">
          {error && (
            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950/30 p-3 rounded">
              {error}
            </div>
          )}

          {/* Global keyword search */}
          {!loading && catalog.length > 0 && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by keyword..."
                value={globalKeywordSearch}
                onChange={e => setGlobalKeywordSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          )}

          {loading && <div className="text-sm py-4">Loading...</div>}
          {!loading && catalog.length === 0 && (
            <div className="text-sm text-muted-foreground py-8 text-center">
              No categories found
            </div>
          )}
          {!loading && globalKeywordSearch && filteredGroups.length === 0 && (
            <div className="text-sm text-muted-foreground py-8 text-center">
              No categories with keywords matching "{globalKeywordSearch}"
            </div>
          )}
          {!loading &&
            filteredGroups.map(group => {
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
                      'w-full flex items-center justify-between px-6 py-4',
                      'transition-all duration-200',
                      'hover:shadow-md',
                      group.bgColor,
                      isExpanded && 'shadow-lg'
                    )}
                  >
                    <div className="flex items-center gap-4">
                      {isExpanded ? (
                        <ChevronDown className="h-5 w-5" />
                      ) : (
                        <ChevronRight className="h-5 w-5" />
                      )}
                      <div className="flex items-center gap-3">
                        {group.icon}
                        <span className={cn('text-lg font-bold', group.color)}>
                          {group.label}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="text-xs">
                        {enabledCount} / {group.categories.length}
                      </Badge>
                    </div>
                  </button>

                  {/* Group Content */}
                  {isExpanded && (
                    <div className="divide-y">
                      {group.categories.map(item => {
                        const catType = getCategoryType(item);
                        const keywordCount = item.keywords?.length || 0;
                        const totalMatches =
                          item.keywords?.reduce(
                            (sum, k) => sum + k.match_count,
                            0
                          ) || 0;

                        return (
                          <div
                            key={item.name}
                            className={cn(
                              'flex items-center justify-between gap-4 px-6 py-3',
                              'hover:bg-accent/50 cursor-pointer',
                              'transition-all duration-150',
                              'hover:scale-[1.01]',
                              !item.enabled && 'opacity-50'
                            )}
                            onClick={() => openKeywordModal(item)}
                            title="Click to manage keywords for this category"
                          >
                            {/* Left: Icon + Name + Badges */}
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                              <span className="text-2xl" aria-hidden>
                                {item.icon}
                              </span>
                              <div className="min-w-0">
                                <div className="font-medium">
                                  {item.display}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  <Badge
                                    variant="outline"
                                    className="text-[10px] h-4 px-1.5"
                                  >
                                    {keywordCount}{' '}
                                    {keywordCount === 1
                                      ? 'keyword'
                                      : 'keywords'}
                                  </Badge>
                                  {totalMatches > 0 && (
                                    <Badge
                                      variant="default"
                                      className="text-[10px] h-4 px-1.5"
                                    >
                                      {totalMatches}{' '}
                                      {totalMatches === 1 ? 'match' : 'matches'}
                                    </Badge>
                                  )}
                                </div>
                              </div>
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
                                <SelectTrigger className="w-[120px] h-8 text-xs">
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
                                  <SelectItem value="transfer">
                                    <span className="flex items-center gap-1.5">
                                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                                      Transfer
                                    </span>
                                  </SelectItem>
                                  <SelectItem value="investment">
                                    <span className="flex items-center gap-1.5">
                                      <span className="w-2 h-2 rounded-full bg-purple-500" />
                                      Investment
                                    </span>
                                  </SelectItem>
                                  <SelectItem value="other">
                                    <span className="flex items-center gap-1.5">
                                      <span className="w-2 h-2 rounded-full bg-gray-500" />
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
