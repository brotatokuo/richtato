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

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const pref = await preferencesApi.get();
        setNotificationsEnabled(pref.notifications_enabled ?? true);
      } catch (e: unknown) {
        setError((e as Error)?.message ?? 'Failed to load preferences');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const updatePreference = async (
    key: 'notifications_enabled',
    value: boolean
  ) => {
    const previous = notificationsEnabled;
    setNotificationsEnabled(value);
    try {
      await preferencesApi.update({ [key]: value });
      toast.success('Notification preference saved');
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to save preferences');
      setNotificationsEnabled(previous);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Bell className="h-4 w-4" />
          Alerts
        </CardTitle>
        <CardDescription>Master notification switch</CardDescription>
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
        </div>
      </CardContent>
    </Card>
  );
}
