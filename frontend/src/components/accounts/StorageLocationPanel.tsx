/**
 * Storage location surface for an account's statement-file directory.
 *
 * Shows the resolved ``storage_uri`` (where statement files are synced,
 * locally or through Google Drive) and the
 * most recent ``StatementFile`` rows the backend scanner has discovered
 * for the account, with their source (manual vs agent drop) and import
 * status.
 *
 * This component is read-only today. The agent and scanner orchestration
 * happens out-of-band: the user runs the host ``bank-agent`` CLI, and
 * Drive-backed accounts upload through the backend for immediate import.
 */
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  statementFileService,
  type StatementFileRecord,
  type StatementFileSource,
} from '@/lib/api/statementFiles';
import { cn } from '@/lib/utils';
import {
  Bot,
  CheckCircle2,
  FileWarning,
  FolderOpen,
  HardDrive,
  Loader2,
  RefreshCw,
  Upload,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface StorageLocationPanelProps {
  accountId: number;
  storageUri?: string;
  resolvedStorageUri?: string;
}

function SourceBadge({ source }: { source: StatementFileSource }) {
  if (source === 'agent_drop') {
    return (
      <Badge
        variant="outline"
        className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30 text-[10px] gap-1"
      >
        <Bot className="h-3 w-3" />
        Agent
      </Badge>
    );
  }
  if (source === 'manual_upload') {
    return (
      <Badge
        variant="outline"
        className="bg-blue-500/10 text-blue-600 dark:text-blue-300 border-blue-500/30 text-[10px] gap-1"
      >
        <Upload className="h-3 w-3" />
        Upload
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-[10px]">
      Unknown
    </Badge>
  );
}

function ImportStatusIcon({ status }: { status: string }) {
  if (status === 'imported') {
    return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />;
  }
  if (status === 'failed') {
    return <FileWarning className="h-3.5 w-3.5 text-destructive" />;
  }
  return <FolderOpen className="h-3.5 w-3.5 text-muted-foreground" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function StorageLocationPanel({
  accountId,
  storageUri,
  resolvedStorageUri,
}: StorageLocationPanelProps) {
  const [files, setFiles] = useState<StatementFileRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = () => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    statementFileService
      .list({ account: accountId })
      .then(response => {
        if (cancelled) return;
        setFiles(response.rows.slice(0, 8));
      })
      .catch(err => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load files');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  };

  useEffect(() => {
    return loadFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const result = await statementFileService.scanAccount(accountId);
      if (result.files_imported > 0) {
        toast.success(
          `${result.files_imported} file${result.files_imported === 1 ? '' : 's'} imported`,
          {
            description: `${result.files_seen} file${result.files_seen === 1 ? '' : 's'} found in storage`,
          }
        );
        loadFiles();
      } else if (result.files_seen === 0) {
        toast.info('No files found in storage');
      } else {
        toast.info(
          `${result.files_seen} file${result.files_seen === 1 ? '' : 's'} found — all already imported`
        );
      }
      if (result.files_failed > 0) {
        toast.warning(
          `${result.files_failed} file${result.files_failed === 1 ? '' : 's'} failed to import`
        );
      }
    } catch (err) {
      toast.error('Scan failed', {
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    } finally {
      setScanning(false);
    }
  };

  const isOverride = Boolean(storageUri);
  const displayUri = resolvedStorageUri || storageUri || '';
  const isDrive = displayUri.startsWith('gdrive://');

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border bg-muted/20 p-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <HardDrive className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-xs font-medium text-foreground">
                Statement storage
              </p>
              {isDrive && (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30"
                >
                  Google Drive
                </Badge>
              )}
              {isOverride && !isDrive && (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-300 border-amber-500/30"
                >
                  Overridden
                </Badge>
              )}
            </div>
            <p
              className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground"
              title={displayUri}
            >
              {displayUri || 'Not configured'}
            </p>
            <p className="mt-1 text-[11px] text-muted-foreground/70">
              {isDrive
                ? 'Statements sync to this account folder in Google Drive.'
                : 'The host bank-agent writes downloads here. Files are auto-imported when the backend scanner runs.'}
            </p>
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-medium text-muted-foreground">
            Recent files
          </p>
          <Button
            size="sm"
            variant="outline"
            className="h-6 px-2 text-[11px]"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="mr-1 h-3 w-3" />
            )}
            Scan for new files
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-6">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <p className="text-xs text-destructive">{error}</p>
        ) : files.length === 0 ? (
          <div className="rounded-md border border-dashed border-border bg-muted/20 px-3 py-4 text-center">
            <FolderOpen className="mx-auto h-5 w-5 text-muted-foreground/40" />
            <p className="mt-1 text-xs text-muted-foreground/70">
              No files in storage yet.
            </p>
          </div>
        ) : (
          <ul className="space-y-1.5">
            {files.map(file => (
              <li
                key={file.id}
                className={cn(
                  'flex items-center gap-2 rounded-md border border-border/60 bg-card px-3 py-2'
                )}
              >
                <ImportStatusIcon status={file.import_status} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p
                      className="truncate text-xs font-medium text-foreground"
                      title={file.original_filename}
                    >
                      {file.original_filename}
                    </p>
                    <SourceBadge source={file.source} />
                  </div>
                  <p className="text-[11px] text-muted-foreground/70">
                    {file.statement_year}-
                    {String(file.statement_month).padStart(2, '0')} ·{' '}
                    {formatSize(file.size_bytes)} ·{' '}
                    {formatDate(file.created_at)}
                  </p>
                </div>
                <span className="ml-2 shrink-0 text-[11px] text-muted-foreground/70">
                  {file.imported_count > 0
                    ? `${file.imported_count} imported`
                    : file.import_status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
