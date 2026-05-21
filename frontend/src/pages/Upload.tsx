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
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Pagination } from '@/components/ui/Pagination';
import { SortableHeader } from '@/components/ui/SortableHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { CloudUpload, Download, Folder, RefreshCw, Trash2 } from 'lucide-react';
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

const PREVIEW_PAGE_SIZE = 25;

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
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [librarySortField, setLibrarySortField] = useState('period');
  const [librarySortDir, setLibrarySortDir] = useState<'asc' | 'desc'>('desc');
  const [previewPage, setPreviewPage] = useState(1);

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

  const sortedStatementRows = useMemo(() => {
    return [...statementRows].sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;
      switch (librarySortField) {
        case 'original_filename':
          aVal = a.original_filename;
          bVal = b.original_filename;
          break;
        case 'account_name':
          aVal = a.account_name;
          bVal = b.account_name;
          break;
        case 'period':
          aVal = a.statement_year * 100 + a.statement_month;
          bVal = b.statement_year * 100 + b.statement_month;
          break;
        case 'import_status':
          aVal = a.import_status;
          bVal = b.import_status;
          break;
        case 'parsed_count':
          aVal = a.parsed_count;
          bVal = b.parsed_count;
          break;
        default:
          return 0;
      }
      if (aVal < bVal) return librarySortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return librarySortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [statementRows, librarySortField, librarySortDir]);

  const handleLibrarySort = (field: string) => {
    if (librarySortField === field) {
      setLibrarySortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setLibrarySortField(field);
      setLibrarySortDir('asc');
    }
  };

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

  useEffect(() => {
    setPreviewPage(1);
  }, [preview]);

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
      {showUploadForm && (
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <CardTitle>Upload Statement</CardTitle>
                <CardDescription>
                  Save a CSV or Excel statement into your local library.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowUploadForm(false)}
              >
                Hide
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
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

            <div className="grid gap-3 lg:grid-cols-[1fr_auto] lg:items-center">
              <div
                className={`rounded-lg border border-dashed p-4 transition-colors ${
                  isDragOver
                    ? 'border-primary bg-primary/5'
                    : 'border-muted-foreground/25 hover:border-muted-foreground/50'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <CloudUpload className="h-6 w-6 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">
                        {selectedFile ? selectedFile.name : 'Drop a file here'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {selectedFile
                          ? formatFileSize(selectedFile.size)
                          : 'CSV, XLS, or XLSX'}
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() =>
                      document.getElementById('file-input')?.click()
                    }
                    variant="outline"
                    size="sm"
                  >
                    Choose File
                  </Button>
                  <input
                    id="file-input"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={e => handleFileSelect(e.target.files)}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
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
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>Statement Library</CardTitle>
              <CardDescription>
                Browse local statements by account, year, and month.
              </CardDescription>
            </div>
            <Button onClick={() => setShowUploadForm(true)}>
              <CloudUpload className="mr-2 h-4 w-4" />
              Upload Statement
            </Button>
          </div>
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

            <div className="rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      <SortableHeader
                        label="File"
                        field="original_filename"
                        sortField={librarySortField}
                        sortDirection={librarySortDir}
                        onSort={handleLibrarySort}
                      />
                    </TableHead>
                    <TableHead>
                      <SortableHeader
                        label="Account"
                        field="account_name"
                        sortField={librarySortField}
                        sortDirection={librarySortDir}
                        onSort={handleLibrarySort}
                      />
                    </TableHead>
                    <TableHead>
                      <SortableHeader
                        label="Period"
                        field="period"
                        sortField={librarySortField}
                        sortDirection={librarySortDir}
                        onSort={handleLibrarySort}
                      />
                    </TableHead>
                    <TableHead>
                      <SortableHeader
                        label="Status"
                        field="import_status"
                        sortField={librarySortField}
                        sortDirection={librarySortDir}
                        onSort={handleLibrarySort}
                      />
                    </TableHead>
                    <TableHead className="text-right">
                      <SortableHeader
                        label="Rows"
                        field="parsed_count"
                        sortField={librarySortField}
                        sortDirection={librarySortDir}
                        onSort={handleLibrarySort}
                        align="right"
                      />
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLibraryLoading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center">
                        <div className="flex items-center justify-center">
                          <LoadingSpinner />
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : sortedStatementRows.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="py-8 text-center text-muted-foreground"
                      >
                        No statements in this folder yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    sortedStatementRows.map(statement => (
                      <TableRow
                        key={statement.id}
                        className="cursor-pointer"
                        data-state={
                          selectedStatement?.id === statement.id
                            ? 'selected'
                            : undefined
                        }
                        onClick={() => setSelectedStatement(statement)}
                      >
                        <TableCell className="max-w-xs truncate">
                          {statement.original_filename}
                        </TableCell>
                        <TableCell>{statement.account_name}</TableCell>
                        <TableCell>
                          {statement.statement_year}-
                          {statement.statement_month
                            .toString()
                            .padStart(2, '0')}
                        </TableCell>
                        <TableCell>
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
                        </TableCell>
                        <TableCell className="text-right">
                          {statement.parsed_count}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
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

            <div className="rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {preview.rows
                    .slice(
                      (previewPage - 1) * PREVIEW_PAGE_SIZE,
                      previewPage * PREVIEW_PAGE_SIZE
                    )
                    .map(row => (
                      <TableRow key={row.source_row_hash}>
                        <TableCell>
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
                        </TableCell>
                        <TableCell>{row.posted_date}</TableCell>
                        <TableCell className="max-w-md truncate">
                          {row.description}
                        </TableCell>
                        <TableCell className="text-right">
                          {row.amount}
                        </TableCell>
                        <TableCell>{row.transaction_type}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </div>

            {preview.rows.length > PREVIEW_PAGE_SIZE && (
              <Pagination
                currentPage={previewPage}
                totalPages={Math.ceil(preview.rows.length / PREVIEW_PAGE_SIZE)}
                onPageChange={setPreviewPage}
                totalItems={preview.rows.length}
                itemsPerPage={PREVIEW_PAGE_SIZE}
              />
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
