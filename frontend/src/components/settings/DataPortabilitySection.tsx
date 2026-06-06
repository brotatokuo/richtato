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
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { userBackupApi, type BackupImportPreview } from '@/lib/api/userBackup';
import { cn } from '@/lib/utils';
import { AlertTriangle, Download, FileJson, Upload } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

function CountRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function DataPortabilitySection() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [canImport, setCanImport] = useState(false);
  const [importBlockedReason, setImportBlockedReason] = useState<string | null>(
    null
  );
  const [exportingJson, setExportingJson] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BackupImportPreview | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const loadImportStatus = useCallback(async () => {
    setLoadingStatus(true);
    try {
      const status = await userBackupApi.getImportStatus();
      setCanImport(status.can_import);
      setImportBlockedReason(status.reason);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to check import status'
      );
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  useEffect(() => {
    void loadImportStatus();
  }, [loadImportStatus]);

  const handleDownloadJson = async () => {
    setExportingJson(true);
    try {
      await userBackupApi.downloadJsonBackup();
      toast.success('Backup downloaded');
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to download backup'
      );
    } finally {
      setExportingJson(false);
    }
  };

  const handleDownloadCsv = async () => {
    setExportingCsv(true);
    try {
      await userBackupApi.downloadTransactionsCsv({
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      });
      toast.success('Transactions CSV downloaded');
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to download transactions CSV'
      );
    } finally {
      setExportingCsv(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setPreview(null);
  };

  const handlePreview = async () => {
    if (!selectedFile) {
      toast.error('Choose a backup JSON file first');
      return;
    }

    setPreviewing(true);
    try {
      const result = await userBackupApi.previewImport(selectedFile);
      setPreview(result);
      if (!result.valid) {
        toast.error('Backup file has validation errors');
      } else {
        toast.success('Backup preview ready');
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to preview backup'
      );
    } finally {
      setPreviewing(false);
    }
  };

  const handleCommit = async () => {
    if (!selectedFile) return;

    setCommitting(true);
    try {
      const result = await userBackupApi.commitImport(selectedFile);
      toast.success(
        `Imported ${result.imported.transactions} transactions across ${result.imported.accounts} accounts`
      );
      setConfirmOpen(false);
      setSelectedFile(null);
      setPreview(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      navigate('/dashboard');
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to import backup'
      );
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export data
          </CardTitle>
          <CardDescription>
            Download a portable backup of your preferences, categories, budgets,
            accounts, and transactions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Backups exclude Google Drive OAuth tokens and household membership.
            Reconfigure those after restoring on a new account.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button onClick={handleDownloadJson} disabled={exportingJson}>
              {exportingJson ? (
                <LoadingSpinner className="mr-2 h-4 w-4" />
              ) : (
                <FileJson className="mr-2 h-4 w-4" />
              )}
              Download full backup (JSON)
            </Button>
          </div>

          <div className="rounded-lg border border-border p-4 space-y-3">
            <p className="text-sm font-medium">Transactions CSV</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <label
                  htmlFor="csv-start-date"
                  className="text-xs text-muted-foreground"
                >
                  Start date (optional)
                </label>
                <Input
                  id="csv-start-date"
                  type="date"
                  value={startDate}
                  onChange={event => setStartDate(event.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label
                  htmlFor="csv-end-date"
                  className="text-xs text-muted-foreground"
                >
                  End date (optional)
                </label>
                <Input
                  id="csv-end-date"
                  type="date"
                  value={endDate}
                  onChange={event => setEndDate(event.target.value)}
                />
              </div>
            </div>
            <Button
              variant="secondary"
              onClick={handleDownloadCsv}
              disabled={exportingCsv}
            >
              {exportingCsv ? (
                <LoadingSpinner className="mr-2 h-4 w-4" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              Download transactions (CSV)
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Import backup
          </CardTitle>
          <CardDescription>
            Restore a JSON backup onto a brand-new account before creating any
            accounts or transactions manually.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loadingStatus ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <LoadingSpinner className="h-4 w-4" />
              Checking import availability...
            </div>
          ) : !canImport ? (
            <div className="flex items-start gap-2 rounded-lg border border-border bg-muted/40 p-3 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-muted-foreground">
                {importBlockedReason ??
                  'Import is unavailable because this account already has data.'}
              </p>
            </div>
          ) : (
            <>
              <Input
                ref={fileInputRef}
                type="file"
                accept="application/json,.json"
                onChange={handleFileChange}
              />
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  onClick={handlePreview}
                  disabled={!selectedFile || previewing}
                >
                  {previewing ? (
                    <LoadingSpinner className="mr-2 h-4 w-4" />
                  ) : null}
                  Preview import
                </Button>
                <Button
                  onClick={() => setConfirmOpen(true)}
                  disabled={!preview?.valid || committing}
                >
                  Import backup
                </Button>
              </div>
            </>
          )}

          {preview ? (
            <div
              className={cn(
                'rounded-lg border p-4 space-y-3',
                preview.valid ? 'border-border' : 'border-destructive/40'
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">
                  {preview.valid ? 'Ready to import' : 'Validation failed'}
                </p>
                {preview.source_profile.username ? (
                  <p className="text-xs text-muted-foreground">
                    From {preview.source_profile.username}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1">
                <CountRow
                  label="Categories"
                  value={preview.counts.categories}
                />
                <CountRow label="Budgets" value={preview.counts.budgets} />
                <CountRow label="Accounts" value={preview.counts.accounts} />
                <CountRow
                  label="Transactions"
                  value={preview.counts.transactions}
                />
              </div>
              {preview.warnings.length > 0 ? (
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Warnings
                  </p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {preview.warnings.map(warning => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {preview.errors.length > 0 ? (
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase tracking-wide text-destructive">
                    Errors
                  </p>
                  <ul className="space-y-1 text-sm text-destructive">
                    {preview.errors.map(error => (
                      <li key={error}>{error}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Import backup?</AlertDialogTitle>
            <AlertDialogDescription>
              This replaces your default categories and loads all accounts,
              budgets, and transactions from the backup file. This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={committing}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={event => {
                event.preventDefault();
                void handleCommit();
              }}
              disabled={committing}
            >
              {committing ? 'Importing...' : 'Import backup'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
