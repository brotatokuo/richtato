import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTheme } from '@/contexts/useTheme';
import { preferencesApi, type PreferenceFieldChoices } from '@/lib/api/user';
import { Palette } from 'lucide-react';
import { useEffect, useState } from 'react';

export function AppearanceSection() {
  const { setTheme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState({
    theme: 'system',
    currency: 'USD',
    dateFormat: 'MM/DD/YYYY',
    timezone: 'UTC',
  });
  const [fieldChoices, setFieldChoices] =
    useState<PreferenceFieldChoices | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [pref, choices] = await Promise.all([
          preferencesApi.get(),
          preferencesApi.getFieldChoices(),
        ]);
        setFieldChoices(choices);
        setSettings(prev => ({
          ...prev,
          theme: (pref.theme as any) || prev.theme,
          currency: pref.currency || prev.currency,
          dateFormat: (pref.date_format as any) || prev.dateFormat,
          timezone: pref.timezone || prev.timezone,
        }));
      } catch (e: any) {
        setError(e?.message ?? 'Failed to load preferences');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const savePrefs = async (next: Partial<typeof settings>) => {
    const updated = { ...settings, ...next };
    setSettings(updated);
    try {
      await preferencesApi.update({
        theme: updated.theme as any,
        currency: updated.currency,
        date_format: updated.dateFormat,
        timezone: updated.timezone,
      });
      if (updated.theme === 'light' || updated.theme === 'dark') {
        setTheme(updated.theme);
      } else if (updated.theme === 'system') {
        const prefersDark = window.matchMedia(
          '(prefers-color-scheme: dark)'
        ).matches;
        setTheme(prefersDark ? 'dark' : 'light');
      }
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save preferences');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Palette className="h-5 w-5" />
          Appearance
        </CardTitle>
        <CardDescription>Customize the look and feel</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-sm text-red-600">{error}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={settings.theme}
              onValueChange={value => savePrefs({ theme: value })}
              disabled={loading || !fieldChoices}
            >
              <SelectTrigger id="theme">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {fieldChoices?.theme.map(choice => (
                  <SelectItem key={choice.value} value={choice.value}>
                    {choice.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="date-format">Date Format</Label>
            <Select
              value={settings.dateFormat}
              onValueChange={value => savePrefs({ dateFormat: value })}
              disabled={loading || !fieldChoices}
            >
              <SelectTrigger id="date-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {fieldChoices?.date_format.map(choice => (
                  <SelectItem key={choice.value} value={choice.value}>
                    {choice.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="currency">Currency</Label>
            <Select
              value={settings.currency}
              onValueChange={value => savePrefs({ currency: value })}
              disabled={loading || !fieldChoices}
            >
              <SelectTrigger id="currency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {fieldChoices?.currency.map(choice => (
                  <SelectItem key={choice.value} value={choice.value}>
                    {choice.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="timezone">Timezone</Label>
            <Select
              value={settings.timezone}
              onValueChange={value => savePrefs({ timezone: value })}
              disabled={loading || !fieldChoices}
            >
              <SelectTrigger id="timezone">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {fieldChoices?.timezone.map(choice => (
                  <SelectItem key={choice.value} value={choice.value}>
                    {choice.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
