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
import { cn } from '@/lib/utils';
import { Bell } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

function NotificationRow({
  id,
  label,
  description,
  checked,
  disabled,
  onCheckedChange,
  className,
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (value: boolean) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0',
        className
      )}
    >
      <div className="min-w-0 space-y-0.5">
        <Label htmlFor={id}>{label}</Label>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
        className="shrink-0"
      />
    </div>
  );
}

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
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Bell className="h-4 w-4" />
          Alerts
        </CardTitle>
        <CardDescription>
          Master notification switch plus bank sync delivery options
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && <div className="mb-4 text-sm text-destructive">{error}</div>}

        <div className="divide-y divide-border">
          <NotificationRow
            id="notifications"
            label="Enable notifications"
            description="Master switch for account notifications"
            checked={notificationsEnabled}
            disabled={loading}
            onCheckedChange={value =>
              void updatePreference('notifications_enabled', value)
            }
          />

          <div className="py-4">
            <p className="text-sm font-medium">Bank sync</p>
            <p className="mt-1 text-sm text-muted-foreground">
              In-app alerts are on by default. Email alerts are opt-in.
            </p>
            <div className="mt-2 divide-y divide-border">
              <NotificationRow
                id="bank-sync-in-app"
                label="In-app alerts"
                description="Failed sync, setup gaps, and re-login prompts in Richtato"
                checked={bankSyncInApp}
                disabled={loading || !notificationsEnabled}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_in_app_notifications', value)
                }
              />
              <NotificationRow
                id="bank-sync-email"
                label="Immediate email alerts"
                description="Email when polling fails or a bank login needs re-auth"
                checked={bankSyncEmail}
                disabled={loading || !notificationsEnabled}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_email_notifications', value)
                }
              />
              <NotificationRow
                id="bank-sync-digest"
                label="Daily digest"
                description="Include bank sync health in the scheduled summary email"
                checked={bankSyncDailyDigest}
                disabled={loading || !notificationsEnabled}
                onCheckedChange={value =>
                  void updatePreference('bank_sync_daily_digest', value)
                }
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
