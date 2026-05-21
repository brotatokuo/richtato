import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CloudUpload,
  Download,
  FileText,
  Folder,
  RefreshCw,
  ShieldCheck,
  Trash2,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  statementImportService,
  type StatementImportResult,
  type StatementInstitution,
} from '@/lib/api/statementImport';
import {
  statementFileService,
  type StatementFileRecord,
  type StatementFolderAccount,
  type StatementStatus,
} from '@/lib/api/statementFiles';
import { transactionsApiService, type Account } from '@/lib/api/transactions';

export function Upload() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [institutions, setInstitutions] = useState<StatementInstitution[]>([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [selectedInstitution, setSelectedInstitution] = useState('');
  const [statementPeriod, setStatementPeriod] = useState('');
  const [statementStatus, setStatementStatus] =
    useState<StatementStatus>('provisional');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [storedStatement, setStoredStatement] =
    useState<StatementFileRecord | null>(null);
  const [preview, setPreview] = useState<StatementImportResult | null>(null);
  const [statementRows, setStatementRows] = useState<StatementFileRecord[]>([]);
  const [folderTree, setFolderTree] = useState<StatementFolderAccount[]>([]);
  const [libraryAccount, setLibraryAccount] = useState('');
  const [libraryYear, setLibraryYear] = useState('');
  const [libraryMonth, setLibraryMonth] = useState('');
  const [selectedStatement, setSelectedStatement] =
    useState<StatementFileRecord | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLibraryLoading, setIsLibraryLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const loadLibrary = async (filters?: {
    account?: string;
    year?: string;
    month?: string;
  }) => {
    setIsLibraryLoading(true);
    try {
      const data = await statementFileService.list({
        account: filters?.account ? Number(filters.account) : undefined,
        year: filters?.year ? Number(filters.year) : undefined,
        month: filters?.month ? Number(filters.month) : undefined,
      });
      setStatementRows(data.rows);
      setFolderTree(data.tree);
      setSelectedStatement(current => {
        if (!current) return data.rows[0] ?? null;
        return (
          data.rows.find(row => row.id === current.id) ?? data.rows[0] ?? null
        );
      });
    } catch (error) {
      toast.error('Unable to load statement library', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsLibraryLoading(false);
    }
  };

  useEffect(() => {
    const loadImportOptions = async () => {
      try {
        const [accountRows, institutionRows] = await Promise.all([
          transactionsApiService.getAccounts(),
          statementImportService.getInstitutions(),
        ]);
        setAccounts(accountRows);
        setInstitutions(institutionRows);
        if (accountRows[0]) setSelectedAccount(String(accountRows[0].id));
        if (institutionRows[0]) setSelectedInstitution(institutionRows[0].id);
        await loadLibrary();
      } catch (error) {
        toast.error('Unable to load import options', {
          description:
            error instanceof Error ? error.message : 'Please try again.',
        });
      }
    };
    void loadImportOptions();
  }, []);

  const selectedInstitutionName = useMemo(
    () =>
      institutions.find(institution => institution.id === selectedInstitution)
        ?.display_name ?? 'Selected institution',
    [institutions, selectedInstitution]
  );

  const handleFileSelect = (selectedFiles: FileList | null) => {
    const file = selectedFiles?.[0];
    if (!file) return;
    setSelectedFile(file);
    setStoredStatement(null);
    setPreview(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const uploadToLibrary = async (): Promise<StatementFileRecord | null> => {
    if (!selectedFile || !selectedAccount || !selectedInstitution) {
      toast.error('Choose a file, account, and institution first.');
      return null;
    }

    const uploaded = await statementFileService.upload({
      file: selectedFile,
      account: Number(selectedAccount),
      institution: selectedInstitution,
      statementPeriod,
      statementStatus,
    });
    setStoredStatement(uploaded.statement);
    setSelectedStatement(uploaded.statement);
    await loadLibrary({
      account: String(uploaded.statement.account),
      year: String(uploaded.statement.statement_year),
      month: String(uploaded.statement.statement_month),
    });
    if (!uploaded.created) {
      toast.info('Statement already exists in the library', {
        description: uploaded.statement.original_filename,
      });
    }
    return uploaded.statement;
  };

  const previewUpload = async () => {
    setIsSubmitting(true);
    try {
      const statement = storedStatement ?? (await uploadToLibrary());
      if (!statement) return;
      const response = await statementFileService.preview(statement.id);
      setStoredStatement(response.statement);
      setSelectedStatement(response.statement);
      setPreview(response.result);
      await loadLibrary({
        account: String(response.statement.account),
        year: String(response.statement.statement_year),
        month: String(response.statement.statement_month),
      });
      toast.success('Statement saved and previewed', {
        description: `${response.result.parsed_count} rows parsed from ${selectedInstitutionName}.`,
      });
    } catch (error) {
      toast.error('Preview failed', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const importStatement = async (statement: StatementFileRecord | null) => {
    if (!statement) {
      toast.error('Preview or select a statement first.');
      return;
    }
    setIsSubmitting(true);
    try {
      const response = await statementFileService.import(statement.id);
      setStoredStatement(response.statement);
      setSelectedStatement(response.statement);
      setPreview(response.result);
      await loadLibrary({
        account: String(response.statement.account),
        year: String(response.statement.statement_year),
        month: String(response.statement.statement_month),
      });
      toast.success('Statement imported', {
        description: `${response.result.imported_count} new rows, ${response.result.duplicate_count} duplicates skipped.`,
      });
    } catch (error) {
      toast.error('Import failed', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const previewStoredStatement = async (statement: StatementFileRecord) => {
    setIsSubmitting(true);
    try {
      const response = await statementFileService.preview(statement.id);
      setSelectedStatement(response.statement);
      setPreview(response.result);
      await loadLibrary({
        account: String(response.statement.account),
        year: String(response.statement.statement_year),
        month: String(response.statement.statement_month),
      });
      toast.success('Preview refreshed', {
        description: `${response.result.parsed_count} rows parsed.`,
      });
    } catch (error) {
      toast.error('Preview failed', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const removeStatement = async (statement: StatementFileRecord) => {
    try {
      await statementFileService.remove(statement.id);
      if (selectedStatement?.id === statement.id) setSelectedStatement(null);
      await loadLibrary({
        account: libraryAccount,
        year: libraryYear,
        month: libraryMonth,
      });
      toast.success('Statement removed from library');
    } catch (error) {
      toast.error('Unable to remove statement', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  const updateStatement = async (
    statement: StatementFileRecord,
    input: {
      account: number;
      institution: string;
      statement_period: string;
      statement_status: StatementStatus;
    }
  ) => {
    try {
      const updated = await statementFileService.update(statement.id, input);
      setSelectedStatement(updated);
      if (storedStatement?.id === updated.id) setStoredStatement(updated);
      await loadLibrary({
        account: String(updated.account),
        year: String(updated.statement_year),
        month: String(updated.statement_month),
      });
      setLibraryAccount(String(updated.account));
      setLibraryYear(String(updated.statement_year));
      setLibraryMonth(String(updated.statement_month));
      toast.success('Statement moved', {
        description: 'The file was moved to the matching account/month folder.',
      });
    } catch (error) {
      toast.error('Unable to update statement', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  const setLibraryFilters = async (
    account: string,
    year: string,
    month: string
  ) => {
    setLibraryAccount(account);
    setLibraryYear(year);
    setLibraryMonth(month);
    await loadLibrary({ account, year, month });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upload Statement</CardTitle>
            <CardDescription>
              Import CSV or Excel statements exported from your financial
              institutions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Account</Label>
                <Select
                  value={selectedAccount}
                  onValueChange={setSelectedAccount}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose account" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map(account => (
                      <SelectItem key={account.id} value={String(account.id)}>
                        {account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Institution</Label>
                <Select
                  value={selectedInstitution}
                  onValueChange={setSelectedInstitution}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose institution" />
                  </SelectTrigger>
                  <SelectContent>
                    {institutions.map(institution => (
                      <SelectItem key={institution.id} value={institution.id}>
                        {institution.display_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="statement-period">Statement Period</Label>
                <Input
                  id="statement-period"
                  placeholder="2025-06 or Jun 2025"
                  value={statementPeriod}
                  onChange={event => setStatementPeriod(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select
                  value={statementStatus}
                  onValueChange={(value: StatementStatus) =>
                    setStatementStatus(value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="provisional">
                      Current/open statement
                    </SelectItem>
                    <SelectItem value="closed">Closed statement</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-muted-foreground/50'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <CloudUpload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">Drop files here</p>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse your computer
              </p>
              <Button
                onClick={() => document.getElementById('file-input')?.click()}
                variant="outline"
              >
                Choose Files
              </Button>
              <input
                id="file-input"
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                onChange={e => handleFileSelect(e.target.files)}
              />
            </div>

            {selectedFile && (
              <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            )}

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button
                onClick={() => void previewUpload()}
                disabled={isSubmitting || !selectedFile}
                variant="outline"
              >
                Save & Preview
              </Button>
              <Button
                onClick={() => void importStatement(storedStatement)}
                disabled={isSubmitting || !storedStatement}
              >
                Import New Rows
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>CSV/Excel First</CardTitle>
            <CardDescription>
              Manual exports are the source of truth. Current-month statements
              can overlap with later closed statements.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">CSV Files</p>
                <p className="text-sm text-muted-foreground">
                  Bank statements, transaction exports
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-orange-500" />
              <div>
                <p className="font-medium">Excel Files</p>
                <p className="text-sm text-muted-foreground">
                  .xlsx and .xls spreadsheets
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-emerald-500" />
              <div>
                <p className="font-medium">Overlap Safe</p>
                <p className="text-sm text-muted-foreground">
                  Row-level dedup skips previously imported transactions
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Statement Library</CardTitle>
          <CardDescription>
            Files are stored locally by account, year, and month for review and
            re-importing.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 lg:grid-cols-[260px_1fr_320px]">
            <div className="space-y-3">
              <Button
                variant={!libraryAccount ? 'default' : 'outline'}
                className="w-full justify-start"
                onClick={() => void setLibraryFilters('', '', '')}
              >
                <Folder className="mr-2 h-4 w-4" />
                All Statements
              </Button>
              {folderTree.map(account => (
                <div key={account.account_id} className="space-y-2">
                  <Button
                    variant={
                      libraryAccount === String(account.account_id)
                        ? 'default'
                        : 'outline'
                    }
                    className="w-full justify-between"
                    onClick={() =>
                      void setLibraryFilters(String(account.account_id), '', '')
                    }
                  >
                    <span className="truncate">{account.account_name}</span>
                    <Badge variant="secondary">{account.count}</Badge>
                  </Button>
                  {libraryAccount === String(account.account_id) && (
                    <div className="ml-3 space-y-1 border-l border-border pl-3">
                      {account.years.map(year => (
                        <div key={year.year} className="space-y-1">
                          <Button
                            variant={
                              libraryYear === String(year.year)
                                ? 'default'
                                : 'ghost'
                            }
                            className="h-8 w-full justify-between px-2"
                            onClick={() =>
                              void setLibraryFilters(
                                String(account.account_id),
                                String(year.year),
                                ''
                              )
                            }
                          >
                            <span>{year.year}</span>
                            <span className="text-xs text-muted-foreground">
                              {year.count}
                            </span>
                          </Button>
                          {libraryYear === String(year.year) && (
                            <div className="ml-3 grid grid-cols-3 gap-1">
                              {year.months.map(month => (
                                <Button
                                  key={month.month}
                                  variant={
                                    libraryMonth === String(month.month)
                                      ? 'default'
                                      : 'ghost'
                                  }
                                  className="h-8 px-2 text-xs"
                                  onClick={() =>
                                    void setLibraryFilters(
                                      String(account.account_id),
                                      String(year.year),
                                      String(month.month)
                                    )
                                  }
                                >
                                  {month.month.toString().padStart(2, '0')}
                                </Button>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">File</th>
                    <th className="px-3 py-2 text-left font-medium">Account</th>
                    <th className="px-3 py-2 text-left font-medium">Period</th>
                    <th className="px-3 py-2 text-left font-medium">Status</th>
                    <th className="px-3 py-2 text-right font-medium">Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {statementRows.map(statement => (
                    <tr
                      key={statement.id}
                      className={`cursor-pointer border-t ${
                        selectedStatement?.id === statement.id
                          ? 'bg-muted/60'
                          : ''
                      }`}
                      onClick={() => setSelectedStatement(statement)}
                    >
                      <td className="max-w-xs truncate px-3 py-2">
                        {statement.original_filename}
                      </td>
                      <td className="px-3 py-2">{statement.account_name}</td>
                      <td className="px-3 py-2">
                        {statement.statement_year}-
                        {statement.statement_month.toString().padStart(2, '0')}
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          variant={
                            statement.import_status === 'imported'
                              ? 'default'
                              : statement.import_status === 'failed'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {statement.import_status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-right">
                        {statement.parsed_count}
                      </td>
                    </tr>
                  ))}
                  {!isLibraryLoading && statementRows.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-3 py-8 text-center text-muted-foreground"
                      >
                        No statements in this folder yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <StatementDetailsPanel
              statement={selectedStatement}
              accounts={accounts}
              institutions={institutions}
              onPreview={previewStoredStatement}
              onImport={importStatement}
              onDelete={removeStatement}
              onUpdate={updateStatement}
              disabled={isSubmitting}
            />
          </div>
        </CardContent>
      </Card>

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Import Preview</CardTitle>
            <CardDescription>
              Review new, duplicate, invalid, and possible changed rows before
              importing.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-4">
              <PreviewMetric label="Parsed" value={preview.parsed_count} />
              <PreviewMetric
                label="New"
                value={preview.rows.filter(row => row.status === 'new').length}
              />
              <PreviewMetric
                label="Duplicates"
                value={preview.duplicate_count}
              />
              <PreviewMetric
                label="Needs Review"
                value={preview.possible_changed_count + preview.invalid_count}
              />
            </div>

            {preview.errors.length > 0 && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {preview.errors.map(error => (
                  <p key={error}>{error}</p>
                ))}
              </div>
            )}

            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">Status</th>
                    <th className="px-3 py-2 text-left font-medium">Date</th>
                    <th className="px-3 py-2 text-left font-medium">
                      Description
                    </th>
                    <th className="px-3 py-2 text-right font-medium">Amount</th>
                    <th className="px-3 py-2 text-left font-medium">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.slice(0, 50).map(row => (
                    <tr key={row.source_row_hash} className="border-t">
                      <td className="px-3 py-2">
                        <Badge
                          variant={
                            row.status === 'new'
                              ? 'default'
                              : row.status === 'duplicate'
                                ? 'secondary'
                                : 'destructive'
                          }
                        >
                          {row.status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">{row.posted_date}</td>
                      <td className="max-w-md truncate px-3 py-2">
                        {row.description}
                      </td>
                      <td className="px-3 py-2 text-right">{row.amount}</td>
                      <td className="px-3 py-2">{row.transaction_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {preview.rows.length > 50 && (
              <p className="text-sm text-muted-foreground">
                Showing first 50 rows of {preview.rows.length}.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PreviewMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
    </div>
  );
}

function StatementDetailsPanel({
  statement,
  accounts,
  institutions,
  onPreview,
  onImport,
  onDelete,
  onUpdate,
  disabled,
}: {
  statement: StatementFileRecord | null;
  accounts: Account[];
  institutions: StatementInstitution[];
  onPreview: (statement: StatementFileRecord) => void;
  onImport: (statement: StatementFileRecord) => void;
  onDelete: (statement: StatementFileRecord) => void;
  onUpdate: (
    statement: StatementFileRecord,
    input: {
      account: number;
      institution: string;
      statement_period: string;
      statement_status: StatementStatus;
    }
  ) => void;
  disabled: boolean;
}) {
  const [editAccount, setEditAccount] = useState('');
  const [editInstitution, setEditInstitution] = useState('');
  const [editPeriod, setEditPeriod] = useState('');
  const [editStatus, setEditStatus] = useState<StatementStatus>('provisional');

  useEffect(() => {
    if (!statement) return;
    setEditAccount(String(statement.account));
    setEditInstitution(statement.institution);
    setEditPeriod(
      statement.statement_period ||
        `${statement.statement_year}-${statement.statement_month
          .toString()
          .padStart(2, '0')}`
    );
    setEditStatus(statement.statement_status);
  }, [statement]);

  if (!statement) {
    return (
      <div className="rounded-lg border border-border p-4 text-sm text-muted-foreground">
        Select a statement to view details.
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-lg border border-border p-4">
      <div>
        <p className="text-sm text-muted-foreground">Selected Statement</p>
        <p className="break-words font-medium">{statement.original_filename}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <DetailItem label="Account" value={statement.account_name} />
        <DetailItem label="Institution" value={statement.institution} />
        <DetailItem
          label="Period"
          value={`${statement.statement_year}-${statement.statement_month
            .toString()
            .padStart(2, '0')}`}
        />
        <DetailItem label="Statement" value={statement.statement_status} />
        <DetailItem label="Import" value={statement.import_status} />
        <DetailItem label="Parsed" value={String(statement.parsed_count)} />
        <DetailItem label="Imported" value={String(statement.imported_count)} />
        <DetailItem
          label="Duplicates"
          value={String(statement.duplicate_count)}
        />
      </div>
      <div className="space-y-3 rounded-lg bg-muted/30 p-3">
        <p className="text-sm font-medium">Move or Edit Metadata</p>
        <div className="space-y-2">
          <Label>Account Folder</Label>
          <Select value={editAccount} onValueChange={setEditAccount}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {accounts.map(account => (
                <SelectItem key={account.id} value={String(account.id)}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Institution</Label>
          <Select value={editInstitution} onValueChange={setEditInstitution}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {institutions.map(institution => (
                <SelectItem key={institution.id} value={institution.id}>
                  {institution.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-2">
            <Label>Period</Label>
            <Input
              value={editPeriod}
              placeholder="2025-06"
              onChange={event => setEditPeriod(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={editStatus}
              onValueChange={(value: StatementStatus) => setEditStatus(value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="provisional">Open</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={disabled || !editAccount || !editInstitution}
          onClick={() =>
            onUpdate(statement, {
              account: Number(editAccount),
              institution: editInstitution,
              statement_period: editPeriod,
              statement_status: editStatus,
            })
          }
        >
          Save & Move
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPreview(statement)}
          disabled={disabled}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Preview
        </Button>
        <Button
          size="sm"
          onClick={() => onImport(statement)}
          disabled={disabled}
        >
          Import
        </Button>
        <Button size="sm" variant="outline" asChild>
          <a href={statementFileService.getDownloadUrl(statement.id)}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </a>
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onDelete(statement)}
          disabled={disabled}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Remove
        </Button>
      </div>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="truncate font-medium capitalize">{value || 'None'}</p>
    </div>
  );
}
