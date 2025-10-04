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
import { CategoryCatalogItem, categorySettingsApi } from '@/lib/api/user';
import { Palette } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

export function Settings() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CategoryCatalogItem[]>([]);

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
        const res = await categorySettingsApi.getCatalog();
        setCatalog(res.categories);
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

  const toggleCategory = (name: string, value: boolean) => {
    setCatalog(prev =>
      prev.map(c => (c.name === name ? { ...c, enabled: value } : c))
    );
  };

  const updateBudgetField = (
    name: string,
    field: 'amount' | 'start_date' | 'end_date',
    value: string
  ) => {
    setCatalog(prev =>
      prev.map(c => {
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
      })
    );
  };

  const removeBudget = (name: string) => {
    setCatalog(prev =>
      prev.map(c => (c.name === name ? { ...c, budget: null } : c))
    );
  };

  const save = async () => {
    try {
      setLoading(true);
      await categorySettingsApi.updateSettings(payload);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
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
                onValueChange={value =>
                  setSettings(prev => ({
                    ...prev,
                    appearance: { ...prev.appearance, theme: value },
                  }))
                }
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
              <Label htmlFor="currency">Currency</Label>
              <Select
                value={settings.appearance.currency}
                onValueChange={value =>
                  setSettings(prev => ({
                    ...prev,
                    appearance: { ...prev.appearance, currency: value },
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD ($)</SelectItem>
                  <SelectItem value="EUR">EUR (€)</SelectItem>
                  <SelectItem value="GBP">GBP (£)</SelectItem>
                  <SelectItem value="CAD">CAD (C$)</SelectItem>
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
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor={`end-${item.name}`}>End (optional)</Label>
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
      </div>
    </div>
  );
}
