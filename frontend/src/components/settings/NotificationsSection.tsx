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
import { toast } from 'sonner';

export function NotificationsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [bankSyncInApp, setBankSyncInApp] = useState(true);
  const [bankSyncEmail, setBankSyncEmail] = useState(false);
  const [bankSyncDailyDigest, setBankSyncDailyDigest] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const pref = await preferencesApi.get();
        setNotificationsEnabled(pref.notifications_enabled ?? true);
        setBankSyncInApp(pref.bank_sync_in_app_notifications ?? true);
        setBankSyncEmail(pref.bank_sync_email_notifications ?? false);
        setBankSyncDailyDigest(pref.bank_sync_daily_digest ?? true);
      } catch (e: unknown) {
        setError((e as Error)?.message ?? 'Failed to load preferences');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const updatePreference = async (
    key:
      | 'notifications_enabled'
      | 'bank_sync_in_app_notifications'
      | 'bank_sync_email_notifications'
      | 'bank_sync_daily_digest',
    value: boolean
  ) => {
    const previous = {
      notifications_enabled: notificationsEnabled,
      bank_sync_in_app_notifications: bankSyncInApp,
      bank_sync_email_notifications: bankSyncEmail,
      bank_sync_daily_digest: bankSyncDailyDigest,
    };
    if (key === 'notifications_enabled') setNotificationsEnabled(value);
    if (key === 'bank_sync_in_app_notifications') setBankSyncInApp(value);
    if (key === 'bank_sync_email_notifications') setBankSyncEmail(value);
    if (key === 'bank_sync_daily_digest') setBankSyncDailyDigest(value);
    try {
      await preferencesApi.update({ [key]: value });
      toast.success('Notification preference saved');
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to save preferences');
      setNotificationsEnabled(previous.notifications_enabled);
      setBankSyncInApp(previous.bank_sync_in_app_notifications);
      setBankSyncEmail(previous.bank_sync_email_notifications);
      setBankSyncDailyDigest(previous.bank_sync_daily_digest);
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
        {error && <div className="text-sm text-destructive">{error}</div>}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="notifications">Enable Notifications</Label>
            <div className="text-sm text-muted-foreground">
              Master switch for account notifications
            </div>
          </div>
          <Switch
            id="notifications"
            checked={notificationsEnabled}
            onCheckedChange={value =>
              void updatePreference('notifications_enabled', value)
            }
            disabled={loading}
          />
        </div>
        <div className="rounded-lg border border-border p-4">
          <div className="mb-3">
            <p className="text-sm font-medium">Bank Sync Alerts</p>
            <p className="text-sm text-muted-foreground">
              In-app alerts are the baseline for polling failures and re-login
              prompts. Email alerts are opt-in.
            </p>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label htmlFor="bank-sync-in-app">In-app alerts</Label>
                <div className="text-sm text-muted-foreground">
                  Show failed sync, setup gap, and re-login notifications in
                  Richtato
                </div>
              </div>
              <Switch
                id="bank-sync-in-app"
                checked={bankSyncInApp}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_in_app_notifications', value)
                }
                disabled={loading || !notificationsEnabled}
              />
            </div>
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label htmlFor="bank-sync-email">Immediate email alerts</Label>
                <div className="text-sm text-muted-foreground">
                  Send Resend email when polling fails or a bank login needs
                  re-auth
                </div>
              </div>
              <Switch
                id="bank-sync-email"
                checked={bankSyncEmail}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_email_notifications', value)
                }
                disabled={loading || !notificationsEnabled}
              />
            </div>
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label htmlFor="bank-sync-digest">Daily digest</Label>
                <div className="text-sm text-muted-foreground">
                  Include bank sync health in the scheduled summary email
                </div>
              </div>
              <Switch
                id="bank-sync-digest"
                checked={bankSyncDailyDigest}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_daily_digest', value)
                }
                disabled={loading || !notificationsEnabled}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
