/**
 * Storage location surface for an account's statement-file directory.
 *
 * Shows the resolved ``storage_uri`` (where statement files are synced,
 * locally or through Google Drive) and the
 * most recent ``StatementFile`` rows the backend scanner has discovered
 * for the account, with their source (manual vs agent drop) and import
 * status.
 *
 * Users can upload statements in-app; the agent and scanner orchestration
 * also runs out-of-band via the host ``bank-agent`` CLI.
 */
import { StatementUploadDialog } from '@/components/accounts/StatementUploadDialog';
import { hasReconciliationWarnings } from '@/components/accounts/statementReconciliation';
import { StatementReconciliationSummary } from '@/components/accounts/StatementReconciliationSummary';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  statementFileService,
  type StatementFileRecord,
  type StatementFileSource,
} from '@/lib/api/statementFiles';
import { statementPeriodDisplayLabel } from '@/lib/formatStatementPeriod';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Cloud,
  ExternalLink,
  FileWarning,
  FolderOpen,
  Loader2,
  RefreshCw,
  Trash2,
  Upload,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface StorageLocationPanelProps {
  accountId: number;
  accountName: string;
  institutionSlug?: string;
  storageUri?: string;
  resolvedStorageUri?: string;
  onUploadComplete?: () => void;
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

function ImportStatusIcon({
  status,
  hasWarnings,
}: {
  status: string;
  hasWarnings?: boolean;
}) {
  if (hasWarnings) {
    return <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />;
  }
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
  accountName,
  institutionSlug,
  storageUri,
  resolvedStorageUri,
  onUploadComplete,
}: StorageLocationPanelProps) {
  const [files, setFiles] = useState<StatementFileRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removeTarget, setRemoveTarget] = useState<StatementFileRecord | null>(
    null
  );
  const [removing, setRemoving] = useState(false);

  const loadFiles = () => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    statementFileService
      .list({ account: accountId })
      .then(async response => {
        if (cancelled) return;
        const recentFiles = response.rows.slice(0, 8);
        const refreshedFiles = await Promise.all(
          recentFiles.map(async file => {
            if (file.import_status === 'imported') {
              return file;
            }
            try {
              const previewResult = await statementFileService.preview(file.id);
              return previewResult.statement;
            } catch {
              return file;
            }
          })
        );
        if (cancelled) return;
        setFiles(refreshedFiles);
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
      const storageError =
        result.files_seen === 0 && result.files_failed > 0
          ? result.outcomes?.find(o => o.status === 'failed')?.detail
          : null;

      if (storageError) {
        toast.error('Could not access storage', { description: storageError });
      } else {
        if (result.files_removed > 0) {
          toast.info(
            `Removed ${result.files_removed} stale file${result.files_removed === 1 ? '' : 's'} from the list`,
            {
              description:
                'These files were deleted from Google Drive but were still listed in Richtato.',
            }
          );
        }
        if (result.files_imported > 0) {
          toast.success(
            `${result.files_imported} file${result.files_imported === 1 ? '' : 's'} imported`,
            {
              description: `${result.files_seen} file${result.files_seen === 1 ? '' : 's'} found in storage`,
            }
          );
        } else if (result.files_seen === 0 && result.files_removed === 0) {
          toast.info('No files found in storage');
        } else if (result.files_removed === 0) {
          toast.info(
            `${result.files_seen} file${result.files_seen === 1 ? '' : 's'} found — all already imported`
          );
        }
        loadFiles();
      }
      if (!storageError && result.files_failed > 0) {
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

  const handleRemove = async () => {
    if (!removeTarget) return;

    setRemoving(true);
    try {
      await statementFileService.remove(removeTarget.id);
      toast.success('Statement removed', {
        description: removeTarget.original_filename,
      });
      setRemoveTarget(null);
      loadFiles();
    } catch (err) {
      toast.error('Failed to remove statement', {
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    } finally {
      setRemoving(false);
    }
  };

  const displayUri = resolvedStorageUri || storageUri || '';
  const isDrive = displayUri.startsWith('gdrive://');
  const driveFolderId = isDrive
    ? displayUri.replace('gdrive://', '').split('/')[0]
    : null;
  const driveUrl = driveFolderId
    ? `https://drive.google.com/drive/folders/${driveFolderId}`
    : null;
  const storageReady = isDrive;

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border bg-muted/20 p-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Cloud className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-xs font-medium text-foreground">
                Statement storage
              </p>
              {isDrive ? (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/30"
                >
                  Google Drive
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[10px]">
                  Not configured
                </Badge>
              )}
            </div>
            <p
              className="mt-0.5 break-all font-mono text-[11px] text-muted-foreground"
              title={displayUri}
            >
              {displayUri || 'Activate Google Drive in Setup → Statements'}
            </p>
            <p className="mt-1 text-[11px] text-muted-foreground/70">
              {storageReady
                ? 'Upload here or let the bank agent sync statements into this Google Drive folder.'
                : 'Statement storage requires Google Drive. Connect and activate it in Setup → Statements.'}
            </p>
            {driveUrl && (
              <a
                href={driveUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-primary hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                Open in Google Drive
              </a>
            )}
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2 gap-2">
          <p className="text-xs font-medium text-muted-foreground">
            Recent files
          </p>
          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant="outline"
              className="h-6 px-2 text-[11px]"
              onClick={() => setUploadOpen(true)}
              disabled={!storageReady}
            >
              <Upload className="mr-1 h-3 w-3" />
              Upload
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-6 px-2 text-[11px]"
              onClick={handleScan}
              disabled={scanning || !storageReady}
            >
              {scanning ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="mr-1 h-3 w-3" />
              )}
              Scan
            </Button>
          </div>
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
            {files.map(file => {
              const reconciliationWarnings = hasReconciliationWarnings(
                file.last_import_result
              );
              return (
                <li
                  key={file.id}
                  className={cn(
                    'rounded-md border border-border/60 bg-card px-3 py-2',
                    reconciliationWarnings &&
                      'border-amber-500/40 bg-amber-500/5'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <ImportStatusIcon
                      status={file.import_status}
                      hasWarnings={reconciliationWarnings}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p
                          className="truncate text-xs font-medium text-foreground"
                          title={file.original_filename}
                        >
                          {file.original_filename}
                        </p>
                        <SourceBadge source={file.source} />
                        {reconciliationWarnings && (
                          <Badge
                            variant="outline"
                            className="text-[10px] bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                          >
                            Balance mismatch
                          </Badge>
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground/70">
                        {statementPeriodDisplayLabel(
                          file.statement_period,
                          file.statement_year,
                          file.statement_month
                        )}{' '}
                        · {formatSize(file.size_bytes)} ·{' '}
                        {formatDate(file.created_at)}
                      </p>
                      {reconciliationWarnings && (
                        <div className="mt-2">
                          <StatementReconciliationSummary
                            compact
                            result={file.last_import_result}
                          />
                        </div>
                      )}
                    </div>
                    <div className="ml-2 flex shrink-0 items-center gap-1.5">
                      <span className="text-[11px] text-muted-foreground/70">
                        {file.imported_count > 0
                          ? `${file.imported_count} imported`
                          : file.import_status}
                      </span>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        aria-label={`Remove ${file.original_filename}`}
                        onClick={() => setRemoveTarget(file)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <AlertDialog
        open={removeTarget !== null}
        onOpenChange={open => {
          if (!open && !removing) setRemoveTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove statement file?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes{' '}
              <span className="font-medium text-foreground">
                {removeTarget?.original_filename}
              </span>{' '}
              from Richtato&apos;s statement list and deletes the stored copy in
              Google Drive when it still exists. Imported transactions are not
              deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={removing}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={removing}
              onClick={event => {
                event.preventDefault();
                void handleRemove();
              }}
            >
              {removing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <StatementUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        accountId={accountId}
        accountName={accountName}
        defaultInstitutionSlug={institutionSlug}
        onComplete={() => {
          loadFiles();
          onUploadComplete?.();
        }}
      />
    </div>
  );
}
