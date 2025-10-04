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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useTheme } from '@/contexts/useTheme';
import { transactionsApiService } from '@/lib/api/transactions';
import {
  CategoryCatalogItem,
  cardsApi,
  categorySettingsApi,
  preferencesApi,
} from '@/lib/api/user';
import { Calendar, Palette } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';

export function Settings() {
  const { setTheme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItem[]>([]);
  const [accounts, setAccounts] = useState<{ id: number; name: string }[]>([]);
  const [cardAccounts, setCardAccounts] = useState<
    { id: number; name: string; bank: string }[]
  >([]);

  const startInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const endInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const [settings, setSettings] = useState({
    appearance: {
      theme: 'system',
      currency: 'USD',
      dateFormat: 'MM/DD/YYYY',
    },
  });

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [catalogRes, accountsRes, cardsRes, prefRes] = await Promise.all([
          categorySettingsApi.getCatalog(),
          transactionsApiService.getAccounts(),
          cardsApi.list(),
          preferencesApi.get(),
        ]);
        setCatalog(catalogRes.categories);
        setAccounts(accountsRes.map(a => ({ id: a.id, name: a.name })));
        setCardAccounts(cardsRes);
        if (prefRes) {
          setSettings(prev => ({
            ...prev,
            appearance: {
              theme: (prefRes.theme as any) || prev.appearance.theme,
              currency: prefRes.currency || prev.appearance.currency,
              dateFormat:
                (prefRes.date_format as any) || prev.appearance.dateFormat,
            },
          }));
        }
        setError(null);
      } catch (e: any) {
        setError(e?.message ?? 'Failed to load settings');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const payload = useMemo(() => {
    const enabled = catalog.filter(c => c.enabled).map(c => c.name);
    const disabled = catalog.filter(c => !c.enabled).map(c => c.name);
    const budgets: Record<
      string,
      { amount: number | null; start_date?: string; end_date?: string | null }
    > = {};
    for (const c of catalog) {
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
  }, [catalog]);

  // Build payload on demand (for auto-save scenarios)
  const buildCatalogPayload = (cat: CategoryCatalogItem[]) => {
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

  // Debounced auto-save for category settings
  const saveCatalogTimer = useRef<number | undefined>(undefined);
  const scheduleSaveCatalog = (next: CategoryCatalogItem[]) => {
    if (saveCatalogTimer.current) {
      window.clearTimeout(saveCatalogTimer.current);
    }
    saveCatalogTimer.current = window.setTimeout(async () => {
      try {
        const p = buildCatalogPayload(next);
        await categorySettingsApi.updateSettings(p);
      } catch (e) {
        console.error('Auto-save categories failed', e);
        setError(e instanceof Error ? e.message : 'Failed to auto-save');
      }
    }, 500);
  };

  const toggleCategory = (name: string, value: boolean) => {
    setCatalog(prev => {
      const next = prev.map(c =>
        c.name === name ? { ...c, enabled: value } : c
      );
      scheduleSaveCatalog(next);
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
        if (field === 'amount') {
          return { ...c, budget: { ...current, amount: Number(value) || 0 } };
        }
        if (field === 'end_date') {
          return { ...c, budget: { ...current, end_date: value || null } };
        }
        return { ...c, budget: { ...current, start_date: value } };
      });
      scheduleSaveCatalog(next);
      return next;
    });
  };

  const removeBudget = (name: string) => {
    setCatalog(prev => {
      const next = prev.map(c =>
        c.name === name ? { ...c, budget: null } : c
      );
      scheduleSaveCatalog(next);
      return next;
    });
  };

  const save = async () => {
    try {
      setLoading(true);
      await Promise.all([
        categorySettingsApi.updateSettings(payload),
        preferencesApi.update({
          theme: settings.appearance.theme as any,
          currency: settings.appearance.currency,
          date_format: settings.appearance.dateFormat,
        }),
      ]);
      // Sync theme immediately
      if (
        settings.appearance.theme === 'light' ||
        settings.appearance.theme === 'dark'
      ) {
        setTheme(settings.appearance.theme);
      }
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Appearance
            </CardTitle>
            <CardDescription>
              Customize the look and feel of the application
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="theme">Theme</Label>
              <Select
                value={settings.appearance.theme}
                onValueChange={value => {
                  setSettings(prev => ({
                    ...prev,
                    appearance: { ...prev.appearance, theme: value },
                  }));
                  // Apply theme immediately for user feedback
                  if (value === 'light' || value === 'dark') {
                    setTheme(value);
                  } else if (value === 'system') {
                    const prefersDark = window.matchMedia(
                      '(prefers-color-scheme: dark)'
                    ).matches;
                    setTheme(prefersDark ? 'dark' : 'light');
                  }
                  // Auto-save preference
                  preferencesApi
                    .update({
                      theme: value as any,
                      currency: settings.appearance.currency,
                      date_format: settings.appearance.dateFormat,
                    })
                    .catch(e => {
                      console.error('Auto-save theme failed', e);
                      setError(
                        e instanceof Error ? e.message : 'Failed to auto-save'
                      );
                    });
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="date-format">Date Format</Label>
              <Select
                value={settings.appearance.dateFormat}
                onValueChange={value =>
                  setSettings(prev => ({
                    ...prev,
                    appearance: { ...prev.appearance, dateFormat: value },
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                  <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Categories & Budgets */}
        <Card>
          <CardHeader>
            <CardTitle>Categories & Budgets</CardTitle>
            <CardDescription>
              Enable categories and set optional budgets per category. Budgets
              have no expiry by default.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="text-sm text-red-600" role="alert">
                {error}
              </div>
            )}
            {loading && <div className="text-sm">Loading…</div>}
            {!loading && (
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
                          ref={el => {
                            startInputRefs.current[item.name] = el;
                          }}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          aria-label={`Open calendar for ${item.display} start`}
                          onClick={() => {
                            const el = startInputRefs.current[item.name];
                            if (!el) return;
                            // prefer native picker when available
                            if (typeof (el as any).showPicker === 'function') {
                              (el as any).showPicker();
                            } else {
                              el.focus();
                              el.click();
                            }
                          }}
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
                          ref={el => {
                            endInputRefs.current[item.name] = el;
                          }}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          aria-label={`Open calendar for ${item.display} end`}
                          onClick={() => {
                            const el = endInputRefs.current[item.name];
                            if (!el) return;
                            // prefer native picker when available
                            if (typeof (el as any).showPicker === 'function') {
                              (el as any).showPicker();
                            } else {
                              el.focus();
                              el.click();
                            }
                          }}
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
            )}
            <div className="pt-2 flex justify-end gap-2">
              <Button onClick={save} disabled={loading}>
                Save Changes
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Accounts */}
        <Card>
          <CardHeader>
            <CardTitle>Accounts</CardTitle>
            <CardDescription>All financial accounts on file</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm">Loading…</div>
            ) : accounts.length === 0 ? (
              <div className="text-sm text-muted-foreground">No accounts</div>
            ) : (
              <div className="space-y-2">
                {accounts.map(acc => (
                  <div
                    key={acc.id}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="text-sm font-medium">{acc.name}</div>
                    <div className="text-xs text-muted-foreground">
                      ID {acc.id}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card Accounts */}
        <Card>
          <CardHeader>
            <CardTitle>Cards</CardTitle>
            <CardDescription>Linked card accounts</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm">Loading…</div>
            ) : cardAccounts.length === 0 ? (
              <div className="text-sm text-muted-foreground">No cards</div>
            ) : (
              <div className="space-y-2">
                {cardAccounts.map(card => (
                  <div
                    key={card.id}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="text-sm font-medium">{card.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {card.bank} • ID {card.id}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
