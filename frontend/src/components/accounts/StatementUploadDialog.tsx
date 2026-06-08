import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { MonthYearPicker } from '@/components/ui/MonthYearPicker';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  statementFileService,
  type StatementFileRecord,
  type StatementStatus,
} from '@/lib/api/statementFiles';
import type { StatementImportResult } from '@/lib/api/statementImport';
import { StatementReconciliationSummary } from '@/components/accounts/StatementReconciliationSummary';
import {
  defaultApplyOpeningBalance,
  needsOpeningBalanceConfirmation,
} from '@/components/accounts/statementReconciliation';
import {
  formatSingleMonthPeriod,
  formatStatementPeriodFromRange,
  parseIsoDateString,
  resolveFilingMonth,
  resolveStatementStatusForMonth,
  validateCustomDateRange,
} from '@/lib/formatStatementPeriod';
import { formatCurrency, formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import { DriveRequiredPrompt } from '@/components/DriveRequiredPrompt';
import { Check, FileUp, Loader2, Upload } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';

type PeriodMode = 'single' | 'custom';

const SUPPORTED_EXTENSIONS = ['.csv', '.xls', '.xlsx', '.pdf'];

function isSupportedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some(ext => name.endsWith(ext));
}

interface StatementUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: number;
  accountName: string;
  storageReady?: boolean;
  onComplete?: () => void;
}

export function StatementUploadDialog({
  open,
  onOpenChange,
  accountId,
  accountName,
  storageReady = true,
  onComplete,
}: StatementUploadDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const today = new Date();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [statementStatus, setStatementStatus] =
    useState<StatementStatus>('provisional');
  const [periodMode, setPeriodMode] = useState<PeriodMode>('single');
  const [statementYear, setStatementYear] = useState(today.getFullYear());
  const [statementMonth, setStatementMonth] = useState(today.getMonth() + 1);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [statement, setStatement] = useState<StatementFileRecord | null>(null);
  const [preview, setPreview] = useState<StatementImportResult | null>(null);
  const [applyOpeningBalance, setApplyOpeningBalance] = useState(false);

  const newCount = useMemo(() => {
    if (!preview) return 0;
    return preview.rows.filter(row => row.status === 'new').length;
  }, [preview]);

  const openingBalanceAction = preview?.reconciliation?.opening_balance_action;
  const showOpeningBalanceConfirmation =
    needsOpeningBalanceConfirmation(openingBalanceAction);
  const previewSampleRows = useMemo(
    () => (preview ? preview.rows.slice(0, 8) : []),
    [preview]
  );

  const formatOpeningBalance = (value: string | undefined) => {
    if (!value) return 'None set';
    const parsed = Number(value.replace(/,/g, ''));
    if (Number.isNaN(parsed)) return `$${value}`;
    return formatCurrency(parsed);
  };

  const formatSignedStatementAmount = (
    amount: string | undefined,
    transactionType: 'debit' | 'credit'
  ) => {
    if (!amount) return '—';
    const parsed = Number(amount.replace(/,/g, ''));
    if (Number.isNaN(parsed)) {
      return `${transactionType === 'credit' ? '+' : '-'}$${amount}`;
    }
    const signed = transactionType === 'credit' ? parsed : -parsed;
    const prefix = signed >= 0 ? '+' : '-';
    return `${prefix}${formatCurrency(Math.abs(signed))}`;
  };

  const formatRunningBalance = (value: string | undefined) => {
    if (!value) return '—';
    const parsed = Number(value.replace(/,/g, ''));
    if (Number.isNaN(parsed)) return `$${value}`;
    return formatCurrency(parsed);
  };

  const syncStatementStatusFromPeriod = (year: number, month: number) => {
    setStatementStatus(resolveStatementStatusForMonth(year, month, today));
  };

  const syncStatementStatusFromCustomEndDate = (endDateValue: string) => {
    const endDate = parseIsoDateString(endDateValue);
    if (!endDate) return;
    const filing = resolveFilingMonth(endDate);
    syncStatementStatusFromPeriod(filing.year, filing.month);
  };

  const reset = () => {
    setSelectedFile(null);
    setStatementStatus('provisional');
    setPeriodMode('single');
    setStatementYear(today.getFullYear());
    setStatementMonth(today.getMonth() + 1);
    setCustomStartDate('');
    setCustomEndDate('');
    setStatement(null);
    setPreview(null);
    setApplyOpeningBalance(false);
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
        description: 'Upload a CSV, XLS, XLSX, or PDF statement file.',
      });
      return;
    }
    setSelectedFile(file);
    setStatement(null);
    setPreview(null);
    setApplyOpeningBalance(false);
  };

  const resolveUploadPeriod = (): {
    statementPeriod: string;
    statementYear: number;
    statementMonth: number;
  } | null => {
    if (periodMode === 'single') {
      return {
        statementPeriod: formatSingleMonthPeriod(statementYear, statementMonth),
        statementYear,
        statementMonth,
      };
    }

    const rangeError = validateCustomDateRange(customStartDate, customEndDate);
    if (rangeError) {
      toast.error('Invalid date range', { description: rangeError });
      return null;
    }

    const startDate = parseIsoDateString(customStartDate)!;
    const endDate = parseIsoDateString(customEndDate)!;
    const filing = resolveFilingMonth(endDate);
    return {
      statementPeriod: formatStatementPeriodFromRange(startDate, endDate),
      statementYear: filing.year,
      statementMonth: filing.month,
    };
  };

  const handleUploadAndPreview = async () => {
    if (!selectedFile) {
      toast.error('Choose a statement file first');
      return;
    }

    const period = resolveUploadPeriod();
    if (!period) return;

    setBusy(true);
    try {
      const uploadResult = await statementFileService.upload({
        file: selectedFile,
        account: accountId,
        statementStatus,
        statementYear: period.statementYear,
        statementMonth: period.statementMonth,
        statementPeriod: period.statementPeriod,
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
      setApplyOpeningBalance(
        defaultApplyOpeningBalance(
          previewResult.result.reconciliation?.opening_balance_action
        )
      );
      setStatement(previewResult.statement);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Please try again.';
      if (message.includes('No statement parser configured')) {
        toast.error('No statement parser for this account', {
          description:
            'Set the account institution to a supported bank before uploading.',
        });
      } else {
        toast.error('Upload failed', { description: message });
      }
    } finally {
      setBusy(false);
    }
  };

  const handleImport = async () => {
    if (!statement) return;

    setBusy(true);
    try {
      const importResult = await statementFileService.import(statement.id, {
        applyOpeningBalance:
          showOpeningBalanceConfirmation && applyOpeningBalance,
      });
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
      <DialogContent
        className={cn(
          'flex max-h-[90vh] flex-col gap-4 overflow-hidden',
          preview ? 'max-w-3xl' : 'max-w-lg'
        )}
      >
        <DialogHeader className="shrink-0">
          <DialogTitle>Upload statement</DialogTitle>
          <DialogDescription>
            Store a statement for {accountName} and import transactions into
            Richtato. Files are saved to this account&apos;s Google Drive
            folder.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">
          {!storageReady ? (
            <DriveRequiredPrompt description="Statement uploads are stored in this account's Google Drive folder. Connect and activate Drive before uploading." />
          ) : (
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
                  accept=".csv,.xls,.xlsx,.pdf,application/pdf"
                  className="hidden"
                  onChange={event =>
                    handleFileSelection(event.target.files?.[0] ?? null)
                  }
                />
                <FileUp className="mx-auto h-8 w-8 text-muted-foreground/60" />
                <p className="mt-2 text-sm text-foreground">
                  {selectedFile
                    ? selectedFile.name
                    : 'Drop a statement file here'}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  CSV, XLS, XLSX, or PDF
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
                  <Label>Statement label</Label>
                  <Tabs
                    value={periodMode}
                    onValueChange={value => {
                      const nextMode = value as PeriodMode;
                      setPeriodMode(nextMode);
                      if (nextMode === 'single') {
                        syncStatementStatusFromPeriod(
                          statementYear,
                          statementMonth
                        );
                      } else if (customEndDate) {
                        syncStatementStatusFromCustomEndDate(customEndDate);
                      }
                    }}
                  >
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="single" disabled={busy}>
                        Single month
                      </TabsTrigger>
                      <TabsTrigger value="custom" disabled={busy}>
                        Date range
                      </TabsTrigger>
                    </TabsList>
                    <TabsContent value="single" className="mt-3 space-y-2">
                      <MonthYearPicker
                        year={statementYear}
                        month={statementMonth}
                        onChange={(year, month) => {
                          setStatementYear(year);
                          setStatementMonth(month);
                          syncStatementStatusFromPeriod(year, month);
                        }}
                      />
                    </TabsContent>
                    <TabsContent value="custom" className="mt-3 space-y-3">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="statement-start-date">
                            Start date
                          </Label>
                          <Input
                            id="statement-start-date"
                            type="date"
                            value={customStartDate}
                            disabled={busy}
                            onChange={event =>
                              setCustomStartDate(event.target.value)
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="statement-end-date">End date</Label>
                          <Input
                            id="statement-end-date"
                            type="date"
                            value={customEndDate}
                            disabled={busy}
                            onChange={event => {
                              const value = event.target.value;
                              setCustomEndDate(value);
                              syncStatementStatusFromCustomEndDate(value);
                            }}
                          />
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                  <p className="text-[11px] text-muted-foreground/80">
                    For naming and library sorting only — does not filter
                    imported transactions.
                    {periodMode === 'custom' && (
                      <>
                        {' '}
                        Library sorting uses the{' '}
                        <span className="font-medium text-muted-foreground">
                          end date
                        </span>
                        .
                      </>
                    )}
                  </p>
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
                      <SelectItem value="provisional">
                        Current / open
                      </SelectItem>
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
                    <span>
                      Possible changed: {preview.possible_changed_count}
                    </span>
                  </div>
                  {preview.errors.length > 0 && (
                    <p className="mt-2 text-xs text-destructive">
                      {preview.errors[0]}
                    </p>
                  )}
                  <div className="mt-3">
                    <StatementReconciliationSummary result={preview} />
                  </div>
                  {previewSampleRows.length > 0 && (
                    <div className="mt-3 overflow-x-auto rounded-md border border-border/70">
                      <table className="w-full min-w-[560px] text-xs">
                        <thead className="bg-muted/30 text-muted-foreground">
                          <tr>
                            <th className="px-2 py-1.5 text-left font-medium">
                              Date
                            </th>
                            <th className="px-2 py-1.5 text-left font-medium">
                              Description
                            </th>
                            <th className="px-2 py-1.5 text-right font-medium">
                              Amount
                            </th>
                            <th className="px-2 py-1.5 text-right font-medium">
                              Running balance
                            </th>
                            <th className="px-2 py-1.5 text-left font-medium">
                              Status
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {previewSampleRows.map(row => (
                            <tr
                              key={row.source_row_hash}
                              className="border-t border-border/50"
                            >
                              <td className="px-2 py-1.5 text-muted-foreground">
                                {formatDate(row.posted_date)}
                              </td>
                              <td className="max-w-[280px] truncate px-2 py-1.5 text-foreground">
                                {row.description}
                              </td>
                              <td
                                className={cn(
                                  'px-2 py-1.5 text-right tabular-nums font-medium',
                                  row.transaction_type === 'credit'
                                    ? 'text-emerald-600 dark:text-emerald-300'
                                    : 'text-destructive'
                                )}
                              >
                                {formatSignedStatementAmount(
                                  row.amount,
                                  row.transaction_type
                                )}
                              </td>
                              <td className="px-2 py-1.5 text-right tabular-nums text-muted-foreground">
                                {formatRunningBalance(row.running_balance)}
                              </td>
                              <td className="px-2 py-1.5 capitalize text-muted-foreground">
                                {row.status.replace('_', ' ')}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {preview.rows.length > previewSampleRows.length && (
                        <p className="border-t border-border/50 px-2 py-1.5 text-[11px] text-muted-foreground">
                          Showing first {previewSampleRows.length} of{' '}
                          {preview.rows.length} parsed rows.
                        </p>
                      )}
                    </div>
                  )}
                  {showOpeningBalanceConfirmation && (
                    <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
                      <p className="text-sm font-medium text-foreground">
                        Opening balance
                      </p>
                      <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                        <p>
                          Statement beginning:{' '}
                          {formatOpeningBalance(
                            preview.reconciliation
                              ?.statement_beginning_balance ??
                              preview.balance_summary?.beginning_balance
                          )}
                          {preview.reconciliation?.statement_beginning_date
                            ? ` on ${formatDate(preview.reconciliation.statement_beginning_date)}`
                            : preview.balance_summary?.beginning_date
                              ? ` on ${formatDate(preview.balance_summary.beginning_date)}`
                              : ''}
                        </p>
                        <p>
                          Current account opening balance:{' '}
                          {formatOpeningBalance(
                            preview.reconciliation
                              ?.account_opening_balance_current
                          )}
                          {preview.reconciliation
                            ?.account_opening_balance_date_current
                            ? ` on ${formatDate(preview.reconciliation.account_opening_balance_date_current)}`
                            : ''}
                        </p>
                      </div>
                      <div className="mt-3 space-y-2">
                        <button
                          type="button"
                          onClick={() => setApplyOpeningBalance(false)}
                          className={cn(
                            'relative w-full rounded-lg border-2 px-3 py-2 text-left text-sm transition-all',
                            !applyOpeningBalance
                              ? 'border-primary ring-2 ring-primary/20'
                              : 'border-border hover:border-primary/50'
                          )}
                        >
                          Keep existing opening balance
                          {!applyOpeningBalance && (
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-primary p-0.5 text-primary-foreground">
                              <Check className="h-3 w-3" />
                            </span>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => setApplyOpeningBalance(true)}
                          className={cn(
                            'relative w-full rounded-lg border-2 px-3 py-2 text-left text-sm transition-all',
                            applyOpeningBalance
                              ? 'border-primary ring-2 ring-primary/20'
                              : 'border-border hover:border-primary/50'
                          )}
                        >
                          Update account opening balance to match statement
                          {applyOpeningBalance && (
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-primary p-0.5 text-primary-foreground">
                              <Check className="h-3 w-3" />
                            </span>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="shrink-0 gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={busy}
          >
            Cancel
          </Button>
          {!storageReady ? null : preview ? (
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
              disabled={busy || !selectedFile}
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
