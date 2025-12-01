import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { preferencesApi } from '@/lib/api/user';
import { Bell } from 'lucide-react';
import { useEffect, useState } from 'react';

export function NotificationsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const pref = await preferencesApi.get();
        setNotificationsEnabled(pref.notifications_enabled ?? true);
      } catch (e: any) {
        setError(e?.message ?? 'Failed to load preferences');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const toggleNotifications = async (value: boolean) => {
    setNotificationsEnabled(value);
    try {
      await preferencesApi.update({
        notifications_enabled: value,
      });
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save preferences');
      // Revert on error
      setNotificationsEnabled(!value);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Notifications
        </CardTitle>
        <CardDescription>Manage your notification preferences</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-sm text-red-600">{error}</div>}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="notifications">Enable Notifications</Label>
            <div className="text-sm text-muted-foreground">
              Receive notifications about your finances
            </div>
          </div>
          <Switch
            id="notifications"
            checked={notificationsEnabled}
            onCheckedChange={toggleNotifications}
            disabled={loading}
          />
        </div>
      </CardContent>
    </Card>
  );
}
