import { Badge } from '@/components/ui/badge';
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
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
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
  ExpensePriority,
  categorySettingsApi,
} from '@/lib/api/user';
import { cn } from '@/lib/utils';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Search,
  Tags,
  Trash2,
} from 'lucide-react';
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

  // Add category modal state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryType, setNewCategoryType] = useState<CategoryType>('expense');
  const [newCategoryIcon, setNewCategoryIcon] = useState('📁');
  const [addingCategory, setAddingCategory] = useState(false);

  // Delete confirmation modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [categoryToDelete, setCategoryToDelete] =
    useState<CategoryCatalogItemWithId | null>(null);
  const [deletingCategory, setDeletingCategory] = useState(false);

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
    // All categories are considered enabled - no toggle needed
    const enabled = cat.map(c => c.name);
    const category_types: Record<string, CategoryType> = {};
    for (const c of cat) {
      // Use type field if available, fallback to expense for backward compatibility
      const catType = c.type || 'expense';
      category_types[c.name] = catType as CategoryType;
    }
    return { enabled, disabled: [], category_types };
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

  const toggleEssential = async (categoryId: number, isCurrentlyEssential: boolean) => {
    const newPriority: ExpensePriority = isCurrentlyEssential ? 'non_essential' : 'essential';
    try {
      await categorySettingsApi.updateCategoryExpensePriority(categoryId, newPriority);
      // Update local state
      setCatalog(prev =>
        prev.map(c =>
          c.id === categoryId
            ? { ...c, expense_priority: newPriority, is_essential: newPriority === 'essential' }
            : c
        )
      );
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update essential status');
    }
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

  // Add new category
  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;

    setAddingCategory(true);
    try {
      await categorySettingsApi.createCategory({
        name: newCategoryName.trim(),
        type: newCategoryType,
        icon: newCategoryIcon || '📁',
      });
      await loadCatalog();
      setAddModalOpen(false);
      setNewCategoryName('');
      setNewCategoryType('expense');
      setNewCategoryIcon('📁');
      setError(null);
      // Expand the group to show the new category
      setExpandedGroups(prev => new Set([...prev, newCategoryType]));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create category');
    } finally {
      setAddingCategory(false);
    }
  };

  // Delete category (soft delete)
  const handleDeleteCategory = async () => {
    if (!categoryToDelete) return;

    setDeletingCategory(true);
    try {
      await categorySettingsApi.deleteCategory(categoryToDelete.id);
      await loadCatalog();
      setDeleteModalOpen(false);
      setCategoryToDelete(null);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete category');
    } finally {
      setDeletingCategory(false);
    }
  };

  const openDeleteModal = (category: CategoryCatalogItemWithId) => {
    setCategoryToDelete(category);
    setDeleteModalOpen(true);
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

      {/* Add Category Modal */}
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add New Category</DialogTitle>
            <DialogDescription>
              Create a new category for organizing your transactions.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="category-name">Name</Label>
              <Input
                id="category-name"
                placeholder="e.g., Subscriptions"
                value={newCategoryName}
                onChange={e => setNewCategoryName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAddCategory()}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="category-type">Type</Label>
              <Select
                value={newCategoryType}
                onValueChange={v => setNewCategoryType(v as CategoryType)}
              >
                <SelectTrigger id="category-type">
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
            <div className="grid gap-2">
              <Label htmlFor="category-icon">Icon (emoji)</Label>
              <Input
                id="category-icon"
                placeholder="📁"
                value={newCategoryIcon}
                onChange={e => setNewCategoryIcon(e.target.value)}
                className="w-20 text-center text-xl"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAddModalOpen(false)}
              disabled={addingCategory}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddCategory}
              disabled={addingCategory || !newCategoryName.trim()}
            >
              {addingCategory ? 'Creating...' : 'Create Category'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Delete Category</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{categoryToDelete?.display}"?
              Existing transactions will keep their current category assignment,
              but this category will no longer appear in lists.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteModalOpen(false)}
              disabled={deletingCategory}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteCategory}
              disabled={deletingCategory}
            >
              {deletingCategory ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Tags className="h-5 w-5" />
                Categories
              </CardTitle>
              <CardDescription>
                Manage your transaction categories and types
              </CardDescription>
            </div>
            <Button
              onClick={() => setAddModalOpen(true)}
              className="gap-1.5"
              size="sm"
            >
              <Plus className="h-4 w-4" />
              Add Category
            </Button>
          </div>
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

          {loading && <div className="py-4 flex justify-center"><LoadingSpinner /></div>}
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
                        {group.categories.length}
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
                              'hover:scale-[1.01]'
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

                            {/* Essential Toggle (only for expense categories) */}
                            {catType === 'expense' && (
                              <div
                                onClick={e => e.stopPropagation()}
                                className="flex items-center gap-1.5"
                                title="Mark as essential expense (needs vs wants)"
                              >
                                <span className="text-[10px] text-muted-foreground">
                                  Essential
                                </span>
                                <Switch
                                  checked={item.expense_priority === 'essential' || item.is_essential === true}
                                  onCheckedChange={() =>
                                    toggleEssential(
                                      item.id,
                                      item.expense_priority === 'essential' || item.is_essential === true
                                    )
                                  }
                                  className="data-[state=checked]:bg-green-500"
                                />
                              </div>
                            )}

                            {/* Right: Delete button */}
                            {/* Don't show for Uncategorized */}
                            {item.name.toLowerCase() !== 'uncategorized' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                onClick={e => {
                                  e.stopPropagation();
                                  openDeleteModal(item);
                                }}
                                title="Delete category"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
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
