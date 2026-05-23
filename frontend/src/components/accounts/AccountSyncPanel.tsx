/**
 * Inline per-account sync panel rendered in the Accounts detail view.
 *
 * Drives the bank-automation flow for the currently-selected account:
 * - status chip + per-account Sync Now and Enabled toggle
 * - last/next run timestamps
 * - "Shared connection settings" subsection (cadence, hour, pause/resume,
 *   remove) that applies to every account under the same bank login
 *
 * When the account isn't bound to any bank-automation connection yet,
 * renders a CTA that opens the Chrome-extension connect dialog.
 */
import { ConnectBankDialog } from '@/components/bank-automation/ConnectBankDialog';
import { RunHistory } from '@/components/bank-automation/RunHistory';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
import type { AccountSyncSummary } from '@/hooks/useBankAutomationConnections';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  Link2,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Trash2,
  WifiOff,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

interface AccountSyncPanelProps {
  accountId: number;
  accountName: string;
  sync: AccountSyncSummary | null;
  initialConnectionIds: number[];
  onChange: () => void | Promise<void>;
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

function StatusChip({
  status,
  statusDisplay,
}: {
  status: BankAutomationConnection['status'];
  statusDisplay: string;
}) {
  const statusColor: Record<typeof status, string> = {
    active:
      'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30',
    reauth_required:
      'bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/30',
    disabled: 'bg-muted text-muted-foreground border-border',
    error: 'bg-destructive/10 text-destructive border-destructive/30',
  };
  const Icon =
    status === 'active'
      ? CheckCircle2
      : status === 'reauth_required'
        ? AlertTriangle
        : status === 'disabled'
          ? PauseCircle
          : WifiOff;

  return (
    <Badge
      variant="outline"
      className={cn(
        'flex items-center gap-1 text-xs font-medium',
        statusColor[status]
      )}
    >
      <Icon className="h-3 w-3" />
      {statusDisplay}
    </Badge>
  );
}

export function AccountSyncPanel({
  accountId,
  accountName,
  sync,
  initialConnectionIds,
  onChange,
}: AccountSyncPanelProps) {
  const [showConnect, setShowConnect] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [running, setRunning] = useState(false);
  const [togglingLink, setTogglingLink] = useState(false);
  const [savingCadence, setSavingCadence] = useState(false);
  const [savingHour, setSavingHour] = useState(false);
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    // Reset collapse + busy state when the selected account changes.
    setShowSettings(false);
    setRunning(false);
    setTogglingLink(false);
    setSavingCadence(false);
    setSavingHour(false);
    setRemoving(false);
  }, [accountId]);

  const siblingCount = useMemo(
    () =>
      sync
        ? sync.connection.account_links.filter(l => l.financial_account != null)
            .length
        : 0,
    [sync]
  );

  if (!sync) {
    return (
      <>
        <div className="rounded-lg border border-dashed border-border bg-muted/30 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <Link2 className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  Not connected
                </p>
                <p className="text-xs text-muted-foreground">
                  Connect to a bank login through the Chrome extension to sync
                  statements automatically.
                </p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowConnect(true)}
              className="gap-2"
            >
              <Link2 className="h-3.5 w-3.5" />
              Connect bank
            </Button>
          </div>
        </div>

        <ConnectBankDialog
          open={showConnect}
          onOpenChange={setShowConnect}
          initialConnectionIds={initialConnectionIds}
          onConnected={async () => {
            await onChange();
          }}
        />
      </>
    );
  }

  const { link, connection } = sync;
  const status = connection.status;
  const isPaused = status === 'disabled';
  const isReauthRequired = status === 'reauth_required';

  const handleSyncNow = async () => {
    setRunning(true);
    try {
      await bankAutomationApi.runConnection(connection.id);
      toast.success('Sync queued', {
        description:
          "We'll run it on the next poll (typically under a minute).",
      });
      await onChange();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to queue run');
    } finally {
      setRunning(false);
    }
  };

  const handleToggleLink = async (enabled: boolean) => {
    setTogglingLink(true);
    try {
      await bankAutomationApi.updateAccountLink(link.id, { enabled });
      toast.success(enabled ? 'Sync enabled' : 'Sync paused for this account');
      await onChange();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to toggle sync');
    } finally {
      setTogglingLink(false);
    }
  };

  const handleCadenceChange = async (value: string) => {
    setSavingCadence(true);
    try {
      await bankAutomationApi.updateConnection(connection.id, {
        cadence: value as BankAutomationCadence,
      });
      toast.success('Schedule updated');
      await onChange();
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
      await bankAutomationApi.updateConnection(connection.id, {
        preferred_run_hour_local: Number(value),
      });
      toast.success('Run time updated');
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update run time'
      );
    } finally {
      setSavingHour(false);
    }
  };

  const handlePauseResume = async () => {
    try {
      await bankAutomationApi.updateConnection(connection.id, {
        enabled: isPaused,
      });
      toast.success(isPaused ? 'Connection resumed' : 'Connection paused');
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update connection'
      );
    }
  };

  const handleRemove = async () => {
    if (
      !window.confirm(
        `Remove the "${connection.nickname || connection.institution_name}" connection?\n\n` +
          `Saved cookies will be deleted. ${siblingCount > 1 ? `All ${siblingCount} accounts under this login will stop syncing. ` : ''}` +
          'Account balances and history stay intact.'
      )
    ) {
      return;
    }
    setRemoving(true);
    try {
      await bankAutomationApi.deleteConnection(connection.id);
      toast.success('Connection removed');
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to remove connection'
      );
      setRemoving(false);
    }
  };

  return (
    <div className="space-y-3">
      {isReauthRequired && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
          Your bank session expired. Sign back into{' '}
          {connection.institution_name} in Chrome and click the Richtato
          extension to refresh cookies.
        </div>
      )}

      {connection.last_failure_reason && status === 'error' && (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          Last failure: {connection.last_failure_reason}
        </div>
      )}

      <div className="rounded-lg border border-border bg-muted/20 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <StatusChip
              status={connection.status}
              statusDisplay={connection.status_display}
            />
            <span className="text-xs text-muted-foreground">
              via {connection.institution_name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={link.enabled && !isPaused}
              disabled={togglingLink || isPaused}
              onCheckedChange={handleToggleLink}
              aria-label={`${link.enabled ? 'Disable' : 'Enable'} sync for ${accountName}`}
            />
            <span className="text-xs text-muted-foreground">
              {isPaused
                ? 'Connection paused'
                : link.enabled
                  ? 'Auto-sync on'
                  : 'Auto-sync off'}
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={handleSyncNow}
              disabled={running || isReauthRequired}
              className="h-8 gap-1.5 text-xs"
            >
              {running ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              Sync now
            </Button>
          </div>
        </div>

        <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
          <div className="flex items-center gap-1.5">
            <CalendarClock className="h-3 w-3" />
            <span>
              Last run:{' '}
              <span className="text-foreground">
                {formatDateTime(connection.last_run_at)}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3" />
            <span>
              Last success:{' '}
              <span className="text-foreground">
                {formatDateTime(connection.last_success_at)}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <PlayCircle className="h-3 w-3" />
            <span>
              Next run:{' '}
              <span className="text-foreground">
                {formatDateTime(connection.next_run_at)}
              </span>
            </span>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowSettings(s => !s)}
        className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/40"
        aria-expanded={showSettings}
      >
        <span className="flex items-center gap-1.5">
          {showSettings ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          Shared connection settings
          {siblingCount > 1 && (
            <span className="text-muted-foreground/70">
              ({siblingCount} accounts under this login)
            </span>
          )}
        </span>
      </button>

      {showSettings && (
        <div className="space-y-4 rounded-lg border border-border bg-card p-3">
          {siblingCount > 1 && (
            <p className="text-xs text-muted-foreground">
              These settings apply to all {siblingCount} accounts under{' '}
              <span className="font-medium text-foreground">
                {connection.nickname || connection.institution_name}
              </span>
              .
            </p>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Cadence</Label>
              <Select
                value={connection.cadence}
                onValueChange={handleCadenceChange}
                disabled={savingCadence}
              >
                <SelectTrigger className="h-9">
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

            <div className="space-y-1.5">
              <Label className="text-xs">Preferred run time</Label>
              <Select
                value={String(connection.preferred_run_hour_local)}
                onValueChange={handleHourChange}
                disabled={savingHour || connection.cadence === 'manual'}
              >
                <SelectTrigger className="h-9">
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

          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handlePauseResume}
              className="h-8 gap-1.5 text-xs"
            >
              {isPaused ? (
                <PlayCircle className="h-3.5 w-3.5" />
              ) : (
                <PauseCircle className="h-3.5 w-3.5" />
              )}
              {isPaused ? 'Resume connection' : 'Pause connection'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRemove}
              disabled={removing}
              className="ml-auto h-8 gap-1.5 text-xs text-destructive hover:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Remove connection
            </Button>
          </div>

          <RunHistory connectionId={connection.id} />
        </div>
      )}
    </div>
  );
}
