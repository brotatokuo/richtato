import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import { CloudUpload, FileText, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  statementImportService,
  type StatementImportResult,
  type StatementInstitution,
} from '@/lib/api/statementImport';
import { transactionsApiService, type Account } from '@/lib/api/transactions';

type StatementStatus = 'provisional' | 'closed';

export function Upload() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [institutions, setInstitutions] = useState<StatementInstitution[]>([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [selectedInstitution, setSelectedInstitution] = useState('');
  const [statementPeriod, setStatementPeriod] = useState('');
  const [statementStatus, setStatementStatus] =
    useState<StatementStatus>('provisional');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<StatementImportResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

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

  const submitStatement = async (mode: 'preview' | 'commit') => {
    if (!selectedFile || !selectedAccount || !selectedInstitution) {
      toast.error('Choose a file, account, and institution first.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await statementImportService.submitStatement({
        file: selectedFile,
        account: Number(selectedAccount),
        institution: selectedInstitution,
        statementPeriod,
        statementStatus,
        mode,
      });
      setPreview(result);
      if (mode === 'commit') {
        toast.success('Statement imported', {
          description: `${result.imported_count} new rows, ${result.duplicate_count} duplicates skipped.`,
        });
      } else {
        toast.success('Statement preview ready', {
          description: `${result.parsed_count} rows parsed from ${selectedInstitutionName}.`,
        });
      }
    } catch (error) {
      toast.error(mode === 'commit' ? 'Import failed' : 'Preview failed', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
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
                onClick={() => void submitStatement('preview')}
                disabled={isSubmitting || !selectedFile}
                variant="outline"
              >
                Preview Import
              </Button>
              <Button
                onClick={() => void submitStatement('commit')}
                disabled={isSubmitting || !preview}
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
