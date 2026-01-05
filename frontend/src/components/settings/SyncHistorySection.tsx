import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { SyncJob, syncService } from '@/lib/api/sync';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  History,
  Loader2,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';

export function SyncHistorySection() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [jobs, setJobs] = useState<SyncJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await syncService.getSyncJobs();
      setJobs(data);
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to load sync history');
    } finally {
      setLoading(false);
    }
  };

  // Fetch jobs when expanded
  useEffect(() => {
    if (isExpanded && jobs.length === 0 && !loading) {
      fetchJobs();
    }
    // jobs.length and loading are intentionally not deps - only fetch on expand
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isExpanded]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '—';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getStatusIcon = (status: SyncJob['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadgeClass = (status: SyncJob['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'cancelled':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card>
      <CardHeader
        className="cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Sync History
            </CardTitle>
            <CardDescription>
              View recent bank sync activity
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" className="ml-2">
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-sm text-red-600 py-4">{error}</div>
          ) : jobs.length === 0 ? (
            <div className="text-sm text-muted-foreground py-4">
              No sync history yet. Connect a bank account and sync to see activity here.
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map(job => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <div className="font-medium text-sm">
                        {job.institution_name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(job.started_at)}
                        {job.is_full_sync && (
                          <span className="ml-2 text-blue-600 dark:text-blue-400">
                            • Full sync
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {job.transactions_synced > 0 ? (
                          <span className="text-green-600 dark:text-green-400">
                            +{job.transactions_synced}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                        {job.transactions_skipped > 0 && (
                          <span className="text-muted-foreground ml-1">
                            ({job.transactions_skipped} skipped)
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatDuration(job.duration_seconds)}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusBadgeClass(job.status)}`}
                    >
                      {job.status}
                    </span>
                  </div>
                </div>
              ))}
              {jobs.length > 0 && (
                <div className="pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={e => {
                      e.stopPropagation();
                      fetchJobs();
                    }}
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : null}
                    Refresh
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
