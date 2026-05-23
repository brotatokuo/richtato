/**
 * Run history for one BankLogin.
 *
 * Lazy-loads when expanded so the network call only happens once the user
 * actually opens the section. Reuses the same compact layout we used for
 * bank-automation runs but with the new SyncRun shape.
 */
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { bankSyncApi, type SyncRun } from '@/lib/api/bankSync';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Loader2,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface RunHistoryProps {
  bankLoginId: number;
}

const STATUS_ICON: Record<SyncRun['status'], typeof CheckCircle2> = {
  queued: Loader2,
  running: Loader2,
  completed: CheckCircle2,
  partial: AlertTriangle,
  failed: XCircle,
};

const STATUS_COLOR: Record<SyncRun['status'], string> = {
  queued: 'text-muted-foreground',
  running: 'text-muted-foreground',
  completed: 'text-emerald-600 dark:text-emerald-400',
  partial: 'text-amber-600 dark:text-amber-400',
  failed: 'text-destructive',
};

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—';
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function formatTime(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function RunHistory({ bankLoginId }: RunHistoryProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [runs, setRuns] = useState<SyncRun[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || runs !== null) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const list = await bankSyncApi.listRuns(bankLoginId);
        if (!cancelled) setRuns(list);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load run history'
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [open, runs, bankLoginId]);

  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen(o => !o)}
        className="gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        Run history
      </Button>

      {open && (
        <div className="rounded-md border border-border">
          {loading ? (
            <div className="flex items-center justify-center py-6 text-xs text-muted-foreground">
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> Loading…
            </div>
          ) : error ? (
            <div className="p-3 text-xs text-destructive">{error}</div>
          ) : !runs || runs.length === 0 ? (
            <div className="p-3 text-xs text-muted-foreground">
              No runs yet for this bank login.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {runs.map(run => {
                const Icon = STATUS_ICON[run.status];
                const spinning =
                  run.status === 'running' || run.status === 'queued';
                return (
                  <li
                    key={run.id}
                    className="flex items-start gap-3 px-3 py-2 text-xs"
                  >
                    <Icon
                      className={cn(
                        'mt-0.5 h-4 w-4 shrink-0',
                        STATUS_COLOR[run.status],
                        spinning && 'animate-spin'
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-foreground">
                          {run.status_display}
                        </span>
                        <Badge
                          variant="outline"
                          className="border-0 bg-muted/40 text-[10px] uppercase"
                        >
                          {run.task_kind_display}
                        </Badge>
                        <span className="ml-auto inline-flex items-center gap-1 text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {formatDuration(run.duration_seconds)}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        {formatTime(run.queued_at)}
                        {run.accounts_attempted > 0 && (
                          <span>
                            {' '}
                            • {run.accounts_succeeded}/{run.accounts_attempted}{' '}
                            accounts
                          </span>
                        )}
                        {run.statements_imported > 0 && (
                          <span> • {run.statements_imported} imported</span>
                        )}
                      </div>
                      {run.failure_reason && (
                        <div className="mt-1 text-destructive">
                          {run.failure_kind}: {run.failure_reason}
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
