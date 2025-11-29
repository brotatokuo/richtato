import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { CategoryCatalogItem, categorySettingsApi } from '@/lib/api/user';
import { Calendar } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';

export function CategoriesBudgetsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItem[]>([]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await categorySettingsApi.getCatalog();
        setCatalog(res.categories);
        setError(null);
      } catch (e: any) {
        setError(e?.message ?? 'Failed to load category settings');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const buildPayload = (cat: CategoryCatalogItem[]) => {
    const enabled = cat.filter(c => c.enabled).map(c => c.name);
    const disabled = cat.filter(c => !c.enabled).map(c => c.name);
    const budgets: Record<
      string,
      { amount: number | null; start_date?: string; end_date?: string | null }
    > = {};
    for (const c of cat) {
      if (c.budget) {
        budgets[c.name] = {
          amount: c.budget.amount,
          start_date: c.budget.start_date,
          end_date: c.budget.end_date ?? null,
        };
      } else {
        budgets[c.name] = { amount: null };
      }
    }
    return { enabled, disabled, budgets };
  };

  const saveTimer = useRef<number | undefined>(undefined);
  const scheduleSave = (next: CategoryCatalogItem[]) => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(async () => {
      try {
        const p = buildPayload(next);
        await categorySettingsApi.updateSettings(p);
      } catch (e: any) {
        setError(e?.message ?? 'Failed to auto-save');
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

  const updateBudgetField = (
    name: string,
    field: 'amount' | 'start_date' | 'end_date',
    value: string
  ) => {
    setCatalog(prev => {
      const next = prev.map(c => {
        if (c.name !== name) return c;
        const current = c.budget ?? {
          id: 0,
          amount: 0,
          start_date: new Date().toISOString().slice(0, 10),
          end_date: null as string | null,
        };
        if (field === 'amount')
          return { ...c, budget: { ...current, amount: Number(value) || 0 } };
        if (field === 'end_date')
          return { ...c, budget: { ...current, end_date: value || null } };
        return { ...c, budget: { ...current, start_date: value } };
      });
      scheduleSave(next);
      return next;
    });
  };

  const removeBudget = (name: string) => {
    setCatalog(prev => {
      const next = prev.map(c =>
        c.name === name ? { ...c, budget: null } : c
      );
      scheduleSave(next);
      return next;
    });
  };

  const payload = useMemo(() => buildPayload(catalog), [catalog]);

  const save = async () => {
    try {
      setLoading(true);
      await categorySettingsApi.updateSettings(payload);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save category settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Categories & Budgets
        </CardTitle>
        <CardDescription>
          Enable categories and set optional budgets per category. Budgets have
          no expiry by default.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-sm text-red-600">{error}</div>}
        {loading && <div className="text-sm">Loading…</div>}
        {!loading && (
          <>
            {/* Desktop layout */}
            <div className="hidden md:block">
              <div className="space-y-3">
                {catalog.map(item => (
                  <div
                    key={item.name}
                    className="grid gap-3 md:grid-cols-12 items-center border rounded-md p-3"
                  >
                    <div className="md:col-span-3 flex items-center gap-2">
                      <span aria-hidden>{item.icon}</span>
                      <span>{item.display}</span>
                    </div>
                    <div className="md:col-span-2 flex items-center gap-2">
                      <Label htmlFor={`enabled-${item.name}`}>Enabled</Label>
                      <Switch
                        id={`enabled-${item.name}`}
                        checked={item.enabled}
                        onCheckedChange={val =>
                          toggleCategory(item.name, Boolean(val))
                        }
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor={`amount-${item.name}`}>Budget</Label>
                      <Input
                        id={`amount-${item.name}`}
                        type="number"
                        step="0.01"
                        value={item.budget?.amount ?? ''}
                        placeholder="No budget"
                        onChange={e =>
                          updateBudgetField(item.name, 'amount', e.target.value)
                        }
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor={`start-${item.name}`}>Start</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          id={`start-${item.name}`}
                          type="date"
                          value={item.budget?.start_date ?? ''}
                          onChange={e =>
                            updateBudgetField(
                              item.name,
                              'start_date',
                              e.target.value
                            )
                          }
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          aria-label={`Open calendar for ${item.display} start`}
                        >
                          <Calendar className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor={`end-${item.name}`}>End (optional)</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          id={`end-${item.name}`}
                          type="date"
                          value={item.budget?.end_date ?? ''}
                          onChange={e =>
                            updateBudgetField(
                              item.name,
                              'end_date',
                              e.target.value
                            )
                          }
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          aria-label={`Open calendar for ${item.display} end`}
                        >
                          <Calendar className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="md:col-span-1 flex justify-end">
                      <Button
                        variant="secondary"
                        onClick={() => removeBudget(item.name)}
                        disabled={!item.budget}
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Mobile layout */}
            <div className="md:hidden">
              <div className="space-y-3">
                {catalog.map(item => (
                  <div
                    key={item.name}
                    className="border rounded-md p-3 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span aria-hidden>{item.icon}</span>
                        <span className="font-medium">{item.display}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Label
                          htmlFor={`enabled-${item.name}`}
                          className="text-xs"
                        >
                          Enabled
                        </Label>
                        <Switch
                          id={`enabled-${item.name}`}
                          checked={item.enabled}
                          onCheckedChange={val =>
                            toggleCategory(item.name, Boolean(val))
                          }
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <Label htmlFor={`amount-${item.name}`}>Budget</Label>
                      <Input
                        id={`amount-${item.name}`}
                        type="number"
                        step="0.01"
                        value={item.budget?.amount ?? ''}
                        placeholder="No budget"
                        onChange={e =>
                          updateBudgetField(item.name, 'amount', e.target.value)
                        }
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div className="space-y-1">
                        <Label htmlFor={`start-${item.name}`}>Start</Label>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Input
                            id={`start-${item.name}`}
                            type="date"
                            className="min-w-0 flex-1"
                            value={item.budget?.start_date ?? ''}
                            onChange={e =>
                              updateBudgetField(
                                item.name,
                                'start_date',
                                e.target.value
                              )
                            }
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            className="shrink-0"
                            aria-label={`Open calendar for ${item.display} start`}
                          >
                            <Calendar className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor={`end-${item.name}`}>
                          End (optional)
                        </Label>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Input
                            id={`end-${item.name}`}
                            type="date"
                            className="min-w-0 flex-1"
                            value={item.budget?.end_date ?? ''}
                            onChange={e =>
                              updateBudgetField(
                                item.name,
                                'end_date',
                                e.target.value
                              )
                            }
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            className="shrink-0"
                            aria-label={`Open calendar for ${item.display} end`}
                          >
                            <Calendar className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        variant="secondary"
                        onClick={() => removeBudget(item.name)}
                        disabled={!item.budget}
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
        <div className="pt-2 flex justify-end gap-2">
          <Button onClick={save} disabled={loading}>
            Save Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
