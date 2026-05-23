/**
 * Inline per-account sync panel rendered in the Accounts detail view.
 *
 * Drives the cookie-only bank-sync flow for the currently-selected
 * account:
 * - sync mode badge (auto | upload | manual)
 * - status chip + per-account sync toggle and Sync Now
 * - last/next run timestamps
 * - "Shared login settings" subsection (cadence, hour, pause/resume,
 *   re-sign-in, remove) that applies to every account under the same
 *   bank login
 *
 * When the account isn't bound to any bank-sync login yet, renders a CTA
 * that opens the Connect-bank wizard. The wizard handles the headed
 * Chromium sign-in flow; we never collect a password here.
 */
import { ConnectBankWizard } from '@/components/bank-sync/ConnectBankWizard';
import { RunHistory } from '@/components/bank-sync/RunHistory';
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
import type { AccountSyncSummary } from '@/hooks/useBankSyncLogins';
import {
  bankSyncApi,
  type BankLogin,
  type BankSyncCadence,
} from '@/lib/api/bankSync';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Globe,
  Link2,
  Loader2,
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
  syncMode?: string;
  sync: AccountSyncSummary | null;
  onChange: () => void | Promise<void>;
}

const CADENCES: { value: BankSyncCadence; label: string }[] = [
  { value: 'manual', label: 'Manual only' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
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
  status: BankLogin['status'];
  statusDisplay: string;
}) {
  const statusColor: Record<typeof status, string> = {
    pending_login:
      'bg-blue-500/10 text-blue-600 dark:text-blue-300 border-blue-500/30',
    active:
      'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30',
    needs_reauth:
      'bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/30',
    disabled: 'bg-muted text-muted-foreground border-border',
    error: 'bg-destructive/10 text-destructive border-destructive/30',
  };
  const Icon =
    status === 'active'
      ? CheckCircle2
      : status === 'needs_reauth'
        ? AlertTriangle
        : status === 'disabled'
          ? PauseCircle
          : status === 'pending_login'
            ? Globe
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

function SyncModeBadge({ syncMode }: { syncMode: string }) {
  const map: Record<string, { label: string; className: string }> = {
    auto: {
      label: 'Auto sync',
      className:
        'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30',
    },
    upload: {
      label: 'Upload statements',
      className:
        'bg-blue-500/10 text-blue-600 dark:text-blue-300 border-blue-500/30',
    },
    manual: {
      label: 'Manual entry',
      className: 'bg-muted text-muted-foreground border-border',
    },
  };
  const entry = map[syncMode] || map.manual;
  return (
    <Badge variant="outline" className={cn('text-[10px]', entry.className)}>
      {entry.label}
    </Badge>
  );
}

export function AccountSyncPanel({
  accountId,
  accountName,
  syncMode = 'manual',
  sync,
  onChange,
}: AccountSyncPanelProps) {
  const [showConnect, setShowConnect] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [running, setRunning] = useState(false);
  const [togglingLink, setTogglingLink] = useState(false);
  const [savingCadence, setSavingCadence] = useState(false);
  const [savingHour, setSavingHour] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [reLoggingIn, setReLoggingIn] = useState(false);

  useEffect(() => {
    setShowSettings(false);
    setRunning(false);
    setTogglingLink(false);
    setSavingCadence(false);
    setSavingHour(false);
    setRemoving(false);
    setReLoggingIn(false);
  }, [accountId]);

  const siblingCount = useMemo(
    () => (sync ? (sync.login.synced_accounts || []).length : 0),
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
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-foreground">
                    Not auto-synced
                  </p>
                  <SyncModeBadge syncMode={syncMode} />
                </div>
                <p className="text-xs text-muted-foreground">
                  Sign in to a supported bank in a real browser window and the
                  agent will keep statements up to date.
                </p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowConnect(true)}
              className="gap-2"
            >
              <Globe className="h-3.5 w-3.5" />
              Connect bank
            </Button>
          </div>
        </div>

        <ConnectBankWizard
          open={showConnect}
          onOpenChange={setShowConnect}
          onConnected={async () => {
            await onChange();
          }}
        />
      </>
    );
  }

  const { syncedAccount, login } = sync;
  const status = login.status;
  const isPaused = status === 'disabled';
  const isReauthRequired = status === 'needs_reauth';

  const handleSyncNow = async () => {
    setRunning(true);
    try {
      await bankSyncApi.syncNow(login.id);
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
      await bankSyncApi.updateSyncedAccount(syncedAccount.id, { enabled });
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
      await bankSyncApi.updateLogin(login.id, {
        cadence: value as BankSyncCadence,
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
      await bankSyncApi.updateLogin(login.id, {
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
      await bankSyncApi.updateLogin(login.id, { enabled: isPaused });
      toast.success(isPaused ? 'Login resumed' : 'Login paused');
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to update login'
      );
    }
  };

  const handleReLogin = async () => {
    setReLoggingIn(true);
    try {
      await bankSyncApi.beginLogin(login.id);
      toast.success('Sign-in queued', {
        description:
          'Watch your desktop for a Chromium window to finish sign-in.',
      });
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to queue the sign-in task.'
      );
    } finally {
      setReLoggingIn(false);
    }
  };

  const handleRemove = async () => {
    if (
      !window.confirm(
        `Remove the "${login.nickname || login.institution_name}" bank login?\n\n` +
          `Stored cookies will be deleted. ${siblingCount > 1 ? `All ${siblingCount} accounts under this login will stop syncing. ` : ''}` +
          'Account balances and history stay intact.'
      )
    ) {
      return;
    }
    setRemoving(true);
    try {
      await bankSyncApi.deleteLogin(login.id);
      toast.success('Bank login removed');
      await onChange();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to remove login'
      );
      setRemoving(false);
    }
  };

  return (
    <div className="space-y-3">
      {isReauthRequired && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
          <span>
            Your {login.institution_name} session expired. Sign in again so the
            agent can keep syncing.
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={handleReLogin}
            disabled={reLoggingIn}
            className="gap-2"
          >
            {reLoggingIn ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Globe className="h-3.5 w-3.5" />
            )}
            Sign in again
          </Button>
        </div>
      )}

      {login.last_failure_reason && status === 'error' && (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          Last failure: {login.last_failure_reason}
        </div>
      )}

      <div className="rounded-lg border border-border bg-muted/20 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <StatusChip
              status={login.status}
              statusDisplay={login.status_display}
            />
            <SyncModeBadge syncMode={syncMode} />
            <span className="text-xs text-muted-foreground">
              via {login.institution_name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={syncedAccount.enabled && !isPaused}
              disabled={togglingLink || isPaused}
              onCheckedChange={handleToggleLink}
              aria-label={`${syncedAccount.enabled ? 'Disable' : 'Enable'} sync for ${accountName}`}
            />
            <span className="text-xs text-muted-foreground">
              {isPaused
                ? 'Login paused'
                : syncedAccount.enabled
                  ? 'Auto-sync on'
                  : 'Auto-sync off'}
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={handleSyncNow}
              disabled={running || isReauthRequired || isPaused}
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
                {formatDateTime(login.last_run_at)}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3 w-3" />
            <span>
              Last success:{' '}
              <span className="text-foreground">
                {formatDateTime(login.last_success_at)}
              </span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <PlayCircle className="h-3 w-3" />
            <span>
              Next run:{' '}
              <span className="text-foreground">
                {formatDateTime(login.next_run_at)}
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
          Shared bank login settings
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
                {login.nickname || login.institution_name}
              </span>
              .
            </p>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Cadence</Label>
              <Select
                value={login.cadence}
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
                value={String(login.preferred_run_hour_local)}
                onValueChange={handleHourChange}
                disabled={savingHour || login.cadence === 'manual'}
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
              {isPaused ? 'Resume login' : 'Pause login'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleReLogin}
              disabled={reLoggingIn}
              className="h-8 gap-1.5 text-xs"
            >
              {reLoggingIn ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Globe className="h-3.5 w-3.5" />
              )}
              Sign in again
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRemove}
              disabled={removing}
              className="ml-auto h-8 gap-1.5 text-xs text-destructive hover:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Remove login
            </Button>
          </div>

          <RunHistory bankLoginId={login.id} />
        </div>
      )}
    </div>
  );
}
