import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  statementFileService,
  type StatementFileRecord,
  type StatementStatus,
} from '@/lib/api/statementFiles';
import {
  statementImportService,
  type StatementImportResult,
  type StatementInstitution,
} from '@/lib/api/statementImport';
import { StatementReconciliationSummary } from '@/components/accounts/StatementReconciliationSummary';
import { cn } from '@/lib/utils';
import { FileUp, Loader2, Upload } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';

const SUPPORTED_EXTENSIONS = ['.csv', '.xls', '.xlsx'];

const INSTITUTION_SLUG_TO_PARSER: Record<string, string> = {
  bank_of_america: 'bofa',
  robinhood: 'robinhood_bank',
  robinhood_investments: 'robinhood_investments',
  robinhood_bank: 'robinhood_bank',
};

function resolveParserInstitution(
  slug: string | undefined,
  institutions: StatementInstitution[]
): string {
  if (institutions.length === 0) return '';
  if (!slug) return institutions[0].id;

  const mapped = INSTITUTION_SLUG_TO_PARSER[slug] ?? slug;
  if (institutions.some(item => item.id === mapped)) return mapped;
  if (institutions.some(item => item.id === slug)) return slug;
  return institutions[0].id;
}

function isSupportedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some(ext => name.endsWith(ext));
}

interface StatementUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: number;
  accountName: string;
  defaultInstitutionSlug?: string;
  onComplete?: () => void;
}

export function StatementUploadDialog({
  open,
  onOpenChange,
  accountId,
  accountName,
  defaultInstitutionSlug,
  onComplete,
}: StatementUploadDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const today = new Date();

  const [institutions, setInstitutions] = useState<StatementInstitution[]>([]);
  const [loadingInstitutions, setLoadingInstitutions] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [institution, setInstitution] = useState('');
  const [statementStatus, setStatementStatus] =
    useState<StatementStatus>('provisional');
  const [statementYear, setStatementYear] = useState(today.getFullYear());
  const [statementMonth, setStatementMonth] = useState(today.getMonth() + 1);
  const [dragActive, setDragActive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [statement, setStatement] = useState<StatementFileRecord | null>(null);
  const [preview, setPreview] = useState<StatementImportResult | null>(null);

  const newCount = useMemo(() => {
    if (!preview) return 0;
    return preview.rows.filter(row => row.status === 'new').length;
  }, [preview]);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoadingInstitutions(true);
    statementImportService
      .getInstitutions()
      .then(data => {
        if (cancelled) return;
        setInstitutions(data);
        setInstitution(resolveParserInstitution(defaultInstitutionSlug, data));
      })
      .catch(err => {
        if (cancelled) return;
        toast.error('Unable to load statement parsers', {
          description: err instanceof Error ? err.message : undefined,
        });
      })
      .finally(() => {
        if (!cancelled) setLoadingInstitutions(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, defaultInstitutionSlug]);

  const reset = () => {
    setSelectedFile(null);
    setInstitution(
      resolveParserInstitution(defaultInstitutionSlug, institutions)
    );
    setStatementStatus('provisional');
    setStatementYear(today.getFullYear());
    setStatementMonth(today.getMonth() + 1);
    setStatement(null);
    setPreview(null);
    setDragActive(false);
    setBusy(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) reset();
    onOpenChange(nextOpen);
  };

  const handleFileSelection = (file: File | null) => {
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!isSupportedFile(file)) {
      toast.error('Unsupported file type', {
        description: 'Upload a CSV, XLS, or XLSX statement file.',
      });
      return;
    }
    setSelectedFile(file);
    setStatement(null);
    setPreview(null);
  };

  const handleUploadAndPreview = async () => {
    if (!selectedFile) {
      toast.error('Choose a statement file first');
      return;
    }
    if (!institution) {
      toast.error('Choose an institution parser');
      return;
    }

    setBusy(true);
    try {
      const uploadResult = await statementFileService.upload({
        file: selectedFile,
        account: accountId,
        institution,
        statementStatus,
        statementYear,
        statementMonth,
        statementPeriod: `${statementYear}-${String(statementMonth).padStart(2, '0')}`,
      });

      if (!uploadResult.created) {
        toast.info('This file was already stored', {
          description: 'Previewing the existing statement record.',
        });
      }

      setStatement(uploadResult.statement);
      const previewResult = await statementFileService.preview(
        uploadResult.statement.id
      );
      setPreview(previewResult.result);
      setStatement(previewResult.statement);
    } catch (err) {
      toast.error('Upload failed', {
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleImport = async () => {
    if (!statement) return;

    setBusy(true);
    try {
      const importResult = await statementFileService.import(statement.id);
      const imported = importResult.result.imported_count;
      const warnings = importResult.result.reconciliation_warnings ?? [];

      if (warnings.length > 0) {
        toast.warning('Imported with balance warnings', {
          description: warnings[0],
        });
      } else {
        toast.success(
          `${imported} transaction${imported === 1 ? '' : 's'} imported`,
          {
            description: importResult.statement.original_filename,
          }
        );
      }
      onComplete?.();
      handleOpenChange(false);
    } catch (err) {
      toast.error('Import failed', {
        description: err instanceof Error ? err.message : 'Please try again.',
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload statement</DialogTitle>
          <DialogDescription>
            Store a statement for {accountName} and import transactions into
            Richtato. Files are saved to this account&apos;s Google Drive
            folder.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div
            className={cn(
              'rounded-lg border border-dashed px-4 py-6 text-center transition-colors',
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-border bg-muted/20'
            )}
            onDragEnter={event => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragOver={event => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={event => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={event => {
              event.preventDefault();
              setDragActive(false);
              handleFileSelection(event.dataTransfer.files?.[0] ?? null);
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xls,.xlsx"
              className="hidden"
              onChange={event =>
                handleFileSelection(event.target.files?.[0] ?? null)
              }
            />
            <FileUp className="mx-auto h-8 w-8 text-muted-foreground/60" />
            <p className="mt-2 text-sm text-foreground">
              {selectedFile ? selectedFile.name : 'Drop a statement file here'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              CSV, XLS, or XLSX
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => fileInputRef.current?.click()}
              disabled={busy}
            >
              <Upload className="mr-2 h-4 w-4" />
              Choose file
            </Button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="statement-institution">Institution parser</Label>
              <Select
                value={institution}
                onValueChange={setInstitution}
                disabled={
                  loadingInstitutions || busy || institutions.length === 0
                }
              >
                <SelectTrigger id="statement-institution">
                  <SelectValue placeholder="Select institution" />
                </SelectTrigger>
                <SelectContent>
                  {institutions.map(item => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Statement period</Label>
              <MonthYearPicker
                year={statementYear}
                month={statementMonth}
                onChange={(year, month) => {
                  setStatementYear(year);
                  setStatementMonth(month);
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="statement-status">Statement type</Label>
              <Select
                value={statementStatus}
                onValueChange={value =>
                  setStatementStatus(value as StatementStatus)
                }
                disabled={busy}
              >
                <SelectTrigger id="statement-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="provisional">Current / open</SelectItem>
                  <SelectItem value="closed">Closed statement</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {preview && (
            <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
              <p className="font-medium text-foreground">Preview</p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <span>Parsed rows: {preview.parsed_count}</span>
                <span>New: {newCount}</span>
                <span>Duplicates: {preview.duplicate_count}</span>
                <span>Invalid: {preview.invalid_count}</span>
                <span>Possible changed: {preview.possible_changed_count}</span>
              </div>
              {preview.errors.length > 0 && (
                <p className="mt-2 text-xs text-destructive">
                  {preview.errors[0]}
                </p>
              )}
              <div className="mt-3">
                <StatementReconciliationSummary result={preview} />
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={busy}
          >
            Cancel
          </Button>
          {preview ? (
            newCount > 0 ? (
              <Button type="button" onClick={handleImport} disabled={busy}>
                {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Import {newCount} transaction{newCount === 1 ? '' : 's'}
              </Button>
            ) : (
              <Button
                type="button"
                onClick={() => {
                  onComplete?.();
                  handleOpenChange(false);
                }}
                disabled={busy}
              >
                Done
              </Button>
            )
          ) : (
            <Button
              type="button"
              onClick={handleUploadAndPreview}
              disabled={busy || !selectedFile || !institution}
            >
              {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Upload & preview
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
