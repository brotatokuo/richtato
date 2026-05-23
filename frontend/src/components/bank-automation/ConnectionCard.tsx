import { RunHistory } from '@/components/bank-automation/RunHistory';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  bankAutomationApi,
  type BankAutomationCadence,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { transactionsApiService, type Account } from '@/lib/api/transactions';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Building2,
  CalendarClock,
  CheckCircle2,
  Link2,
  Loader2,
  PauseCircle,
  PlayCircle,
  Trash2,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface ConnectionCardProps {
  connection: BankAutomationConnection;
  onChange: (next: BankAutomationConnection) => void;
  onRemoved: (id: number) => void;
}

const CADENCES: { value: BankAutomationCadence; label: string }[] = [
  { value: 'manual', label: 'Manual only' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Every 2 weeks' },
  { value: 'monthly', label: 'Monthly' },
];

const HOURS = Array.from({ length: 24 }, (_, i) => i);

function formatHour(hour: number): string {
  if (hour === 0) return '12:00 AM';
  if (hour < 12) return `${hour}:00 AM`;
  if (hour === 12) return '12:00 PM';
  return `${hour - 12}:00 PM`;
}

function formatDateTime(value: string | null): string {
  if (!value) return 'Never';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function ConnectionCard({
  connection,
  onChange,
  onRemoved,
}: ConnectionCardProps) {
  const [savingCadence, setSavingCadence] = useState(false);
  const [savingHour, setSavingHour] = useState(false);
  const [running, setRunning] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [bindingLinkId, setBindingLinkId] = useState<number | null>(null);

  const hasUnboundLink = connection.account_links.some(
    link => link.financial_account == null
  );

  useEffect(() => {
    if (!hasUnboundLink || accounts.length > 0) return;
    let cancelled = false;
    transactionsApiService
      .getAccounts()
      .then(rows => {
        if (!cancelled) setAccounts(rows);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [hasUnboundLink, accounts.length]);

  const handleCadenceChange = async (value: string) => {
    setSavingCadence(true);
    try {
      const next = await bankAutomationApi.updateConnection(connection.id, {
        cadence: value as BankAutomationCadence,
      });
      onChange(next);
      toast.success('Schedule updated');
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update cadence'
      );
    } finally {
      setSavingCadence(false);
    }
  };

  const handleHourChange = async (value: string) => {
    setSavingHour(true);
    try {
      const next = await bankAutomationApi.updateConnection(connection.id, {
        preferred_run_hour_local: Number(value),
      });
      onChange(next);
      toast.success('Run time updated');
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update run time'
      );
    } finally {
      setSavingHour(false);
    }
  };

  const handleEnabledChange = async (enabled: boolean) => {
    try {
      const next = await bankAutomationApi.updateConnection(connection.id, {
        enabled,
      });
      onChange(next);
      toast.success(enabled ? 'Connection enabled' : 'Connection paused');
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update connection'
      );
    }
  };

  const handleSyncNow = async () => {
    setRunning(true);
    try {
      await bankAutomationApi.runConnection(connection.id);
      toast.success('Sync queued', {
        description:
          "We'll run it on the next poll (typically under a minute).",
      });
      const refreshed = await bankAutomationApi.getConnection(connection.id);
      onChange(refreshed);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to queue run');
    } finally {
      setRunning(false);
    }
  };

  const handleRemove = async () => {
    if (
      !window.confirm(
        'Remove this connection? Saved cookies will be deleted; the financial accounts stay intact.'
      )
    ) {
      return;
    }
    setRemoving(true);
    try {
      await bankAutomationApi.deleteConnection(connection.id);
      toast.success('Connection removed');
      onRemoved(connection.id);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to remove connection'
      );
      setRemoving(false);
    }
  };

  const handleAccountToggle = async (linkId: number, enabled: boolean) => {
    try {
      await bankAutomationApi.updateAccountLink(linkId, { enabled });
      const refreshed = await bankAutomationApi.getConnection(connection.id);
      onChange(refreshed);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to toggle account'
      );
    }
  };

  const handleBindAccount = async (linkId: number, value: string) => {
    if (!value) return;
    setBindingLinkId(linkId);
    try {
      await bankAutomationApi.updateAccountLink(linkId, {
        financial_account_id: Number(value),
      });
      const refreshed = await bankAutomationApi.getConnection(connection.id);
      onChange(refreshed);
      toast.success('Account bound');
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to bind account'
      );
    } finally {
      setBindingLinkId(null);
    }
  };

  const statusColor: Record<typeof connection.status, string> = {
    active:
      'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    reauth_required:
      'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    disabled: 'bg-muted text-muted-foreground',
    error:
      'bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive',
  };

  const StatusIcon =
    connection.status === 'active'
      ? CheckCircle2
      : connection.status === 'reauth_required'
        ? AlertTriangle
        : connection.status === 'disabled'
          ? PauseCircle
          : AlertTriangle;

  return (
    <Card className="border-border">
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="flex items-start gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <Building2 className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <CardTitle className="truncate text-base">
              {connection.nickname || connection.institution_name}
            </CardTitle>
            <p className="truncate text-xs text-muted-foreground">
              {connection.institution_name} • {connection.account_links.length}{' '}
              account{connection.account_links.length === 1 ? '' : 's'}
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className={cn(
            'flex items-center gap-1 border-0',
            statusColor[connection.status]
          )}
        >
          <StatusIcon className="h-3 w-3" />
          {connection.status_display}
        </Badge>
      </CardHeader>

      <CardContent className="space-y-5">
        {connection.status === 'reauth_required' && (
          <div className="rounded-md border border-amber-500/30 bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
            Your bank session expired. Open the bank in Chrome, sign in, and
            click the Richtato extension to refresh the cookies.
          </div>
        )}

        {connection.last_failure_reason && connection.status === 'error' && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            Last failure: {connection.last_failure_reason}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs">Cadence</Label>
            <Select
              value={connection.cadence}
              onValueChange={handleCadenceChange}
              disabled={savingCadence}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select cadence" />
              </SelectTrigger>
              <SelectContent>
                {CADENCES.map(c => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Preferred run time</Label>
            <Select
              value={String(connection.preferred_run_hour_local)}
              onValueChange={handleHourChange}
              disabled={savingHour || connection.cadence === 'manual'}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select hour" />
              </SelectTrigger>
              <SelectContent>
                {HOURS.map(h => (
                  <SelectItem key={h} value={String(h)}>
                    {formatHour(h)} (your local time)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid gap-2 rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground sm:grid-cols-3">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-3.5 w-3.5" />
            <div>
              <div className="font-medium text-foreground">Last run</div>
              <div>{formatDateTime(connection.last_run_at)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <div>
              <div className="font-medium text-foreground">Last success</div>
              <div>{formatDateTime(connection.last_success_at)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <PlayCircle className="h-3.5 w-3.5" />
            <div>
              <div className="font-medium text-foreground">Next run</div>
              <div>{formatDateTime(connection.next_run_at)}</div>
            </div>
          </div>
        </div>

        {connection.account_links.length === 0 ? (
          <div className="rounded-md border border-amber-500/30 bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
            <div className="font-medium">No accounts captured yet.</div>
            <div className="mt-1 text-xs">
              Open the bank in Chrome, navigate to a specific account&apos;s
              activity page, then click the Richtato extension and press{' '}
              <em>Sync this account to Richtato</em>. Repeat for each account
              you want synced.
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Label className="text-xs">Accounts under this login</Label>
            <ul className="space-y-2">
              {connection.account_links.map(link => {
                const unbound = link.financial_account == null;
                return (
                  <li
                    key={link.id}
                    className={cn(
                      'flex flex-col gap-2 rounded-md border p-2 sm:flex-row sm:items-center sm:justify-between',
                      unbound
                        ? 'border-amber-500/30 bg-amber-50/40 dark:bg-amber-950/20'
                        : 'border-border'
                    )}
                  >
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">
                        {link.detected_account_name ||
                          link.financial_account_name ||
                          'Captured account'}
                      </div>
                      <div className="truncate text-xs text-muted-foreground">
                        {unbound ? (
                          <span className="text-amber-700 dark:text-amber-300">
                            Not yet bound to a Richtato account
                          </span>
                        ) : (
                          <>
                            {link.financial_account_name} • {link.flow}
                          </>
                        )}
                      </div>
                    </div>
                    {unbound ? (
                      <div className="flex items-center gap-2">
                        <Link2 className="h-3.5 w-3.5 text-muted-foreground" />
                        <Select
                          value=""
                          onValueChange={value =>
                            handleBindAccount(link.id, value)
                          }
                          disabled={bindingLinkId === link.id}
                        >
                          <SelectTrigger className="h-8 w-[220px]">
                            <SelectValue
                              placeholder={
                                bindingLinkId === link.id
                                  ? 'Binding…'
                                  : 'Bind to Richtato account'
                              }
                            />
                          </SelectTrigger>
                          <SelectContent>
                            {accounts.map(a => (
                              <SelectItem key={a.id} value={String(a.id)}>
                                {a.name}
                                {a.account_number_last4
                                  ? ` …${a.account_number_last4}`
                                  : ''}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ) : (
                      <Switch
                        checked={link.enabled}
                        onCheckedChange={enabled =>
                          handleAccountToggle(link.id, enabled)
                        }
                        aria-label="Toggle account"
                      />
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={handleSyncNow}
            disabled={running || connection.status === 'reauth_required'}
            className="gap-2"
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <PlayCircle className="h-4 w-4" />
            )}
            Sync now
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              handleEnabledChange(connection.status === 'disabled')
            }
            className="gap-2"
          >
            {connection.status === 'disabled' ? (
              <PlayCircle className="h-4 w-4" />
            ) : (
              <PauseCircle className="h-4 w-4" />
            )}
            {connection.status === 'disabled' ? 'Resume' : 'Pause'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRemove}
            disabled={removing}
            className="ml-auto gap-2 text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            Remove
          </Button>
        </div>

        <RunHistory connectionId={connection.id} />
      </CardContent>
    </Card>
  );
}
