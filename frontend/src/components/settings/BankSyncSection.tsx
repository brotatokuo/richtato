import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  agentFlowLabel,
  bankSyncApi,
  SYNC_MODE_OPTIONS,
  type BankSyncSetupAccount,
  type SyncMode,
} from '@/lib/api/bankSync';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Copy,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  Landmark,
  Loader2,
  RefreshCw,
  Terminal,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const HOST_COMMANDS = [
  'set -a && source richtato-bank-agent.env && set +a',
  'python -m scripts.bank_sync.agent sync-config',
  'python -m scripts.bank_sync.agent status',
  'python -m scripts.bank_sync.agent login signin <login_id>',
  'python -m scripts.bank_sync.agent sync',
] as const;

const AGENT_ENV_FILENAME = 'richtato-bank-agent.env';

interface AgentCredentials {
  token: string;
  fernetKey: string;
}

function maskSecret(value: string): string {
  if (value.length <= 8) return '••••••••';
  return `${value.slice(0, 4)}${'•'.repeat(Math.min(value.length - 8, 24))}${value.slice(-4)}`;
}

function buildAgentEnvFile(credentials: AgentCredentials): string {
  return [
    `RICHTATO_API_TOKEN="${credentials.token}"`,
    `BANK_AGENT_FERNET_KEY="${credentials.fernetKey}"`,
    '',
  ].join('\n');
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

function downloadTextFile(filename: string, contents: string): void {
  const blob = new Blob([contents], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function syncModeBadgeVariant(
  mode: SyncMode
): 'default' | 'secondary' | 'outline' {
  switch (mode) {
    case 'auto':
      return 'default';
    case 'upload':
      return 'secondary';
    default:
      return 'outline';
  }
}

function accountNeedsAttention(account: BankSyncSetupAccount): boolean {
  return (
    account.sync_mode === 'auto' &&
    account.needs_storage_for_auto &&
    !account.has_storage_uri
  );
}

export function BankSyncSection() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [accounts, setAccounts] = useState<BankSyncSetupAccount[]>([]);
  const [agentLoginCount, setAgentLoginCount] = useState(0);
  const [agentAccountCount, setAgentAccountCount] = useState(0);
  const [savingAccountId, setSavingAccountId] = useState<number | null>(null);
  const [credentials, setCredentials] = useState<AgentCredentials | null>(null);
  const [credentialsLoading, setCredentialsLoading] = useState(false);
  const [credentialsVisible, setCredentialsVisible] = useState(false);

  const ensureCredentials = useCallback(async (): Promise<AgentCredentials> => {
    if (credentials) return credentials;
    setCredentialsLoading(true);
    try {
      const payload = await bankSyncApi.getApiToken();
      const nextCredentials = {
        token: payload.token,
        fernetKey: payload.fernet_key,
      };
      setCredentials(nextCredentials);
      return nextCredentials;
    } finally {
      setCredentialsLoading(false);
    }
  }, [credentials]);

  const handleRevealCredentials = async () => {
    if (credentialsVisible) {
      setCredentialsVisible(false);
      return;
    }
    try {
      await ensureCredentials();
      setCredentialsVisible(true);
    } catch (error) {
      toast.error('Unable to load host credentials', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  const handleCopyCredentials = async () => {
    try {
      const nextCredentials = await ensureCredentials();
      await copyTextToClipboard(buildAgentEnvFile(nextCredentials));
      toast.success('Host credentials copied');
    } catch (error) {
      toast.error('Unable to copy host credentials', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  const handleDownloadCredentials = async () => {
    try {
      const nextCredentials = await ensureCredentials();
      downloadTextFile(AGENT_ENV_FILENAME, buildAgentEnvFile(nextCredentials));
      toast.success(`Downloaded ${AGENT_ENV_FILENAME}`);
    } catch (error) {
      toast.error('Unable to download host credentials', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  const loadSetup = useCallback(async (options?: { silent?: boolean }) => {
    if (options?.silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const payload = await bankSyncApi.getSetup();
      setAccounts(payload.accounts);
      setAgentLoginCount(payload.agent_config.logins.length);
      setAgentAccountCount(
        payload.agent_config.logins.reduce(
          (total, login) => total + login.accounts.length,
          0
        )
      );
    } catch (error) {
      toast.error('Unable to load sync settings', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadSetup();
  }, [loadSetup]);

  const attentionCount = useMemo(
    () => accounts.filter(accountNeedsAttention).length,
    [accounts]
  );

  const handleSyncModeChange = async (
    account: BankSyncSetupAccount,
    nextMode: SyncMode
  ) => {
    if (nextMode === account.sync_mode) return;

    if (nextMode === 'auto' && !account.agent_sync_supported) {
      toast.error('Auto sync is not available for this account', {
        description:
          'Pick a supported bank and account type, or use upload/manual.',
      });
      return;
    }

    setSavingAccountId(account.id);
    try {
      await bankSyncApi.updateSyncMode(account.id, nextMode);
      setAccounts(current =>
        current.map(row =>
          row.id === account.id ? { ...row, sync_mode: nextMode } : row
        )
      );
      toast.success(`${account.name} sync mode updated`);
      await loadSetup({ silent: true });
    } catch (error) {
      toast.error('Unable to update sync mode', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setSavingAccountId(null);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Bank Agent Sync
          </CardTitle>
          <CardDescription>
            Choose how each account receives data. Auto-sync accounts are picked
            up by the host Playwright bank-agent running on your desktop.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading sync settings...
            </div>
          ) : (
            <>
              <div className="rounded-lg border border-border bg-muted/20 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant={agentAccountCount > 0 ? 'default' : 'outline'}
                  >
                    {agentAccountCount} auto-sync account
                    {agentAccountCount === 1 ? '' : 's'}
                  </Badge>
                  <Badge variant="outline">
                    {agentLoginCount} bank login
                    {agentLoginCount === 1 ? '' : 's'} in agent config
                  </Badge>
                  {attentionCount > 0 && (
                    <Badge variant="destructive">
                      {attentionCount} need{attentionCount === 1 ? 's' : ''}{' '}
                      Google Drive folder
                    </Badge>
                  )}
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Statement-based banks need Google Drive activated in{' '}
                  <Link
                    to="/setup?tab=statements"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Setup → Statements
                  </Link>
                  . Investment balance banks (Guideline, Robinhood) scrape
                  portfolio values and do not need Drive folders.
                </p>
              </div>

              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-medium">Accounts</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void loadSetup({ silent: true })}
                  disabled={refreshing}
                >
                  {refreshing ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Refresh
                </Button>
              </div>

              {accounts.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                  <Landmark className="mx-auto mb-2 h-5 w-5 opacity-50" />
                  <p>No linked accounts yet.</p>
                  <Link
                    to="/accounts"
                    className="mt-2 inline-flex items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Create accounts
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {accounts.map(account => {
                    const isSaving = savingAccountId === account.id;
                    const needsAttention = accountNeedsAttention(account);
                    const autoDisabled = !account.agent_sync_supported;

                    return (
                      <div
                        key={account.id}
                        className={cn(
                          'rounded-lg border border-border p-4',
                          needsAttention && 'border-amber-500/40 bg-amber-500/5'
                        )}
                      >
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div className="min-w-0 space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="font-medium">{account.name}</p>
                              <Badge
                                variant={syncModeBadgeVariant(
                                  account.sync_mode
                                )}
                              >
                                {SYNC_MODE_OPTIONS.find(
                                  option => option.value === account.sync_mode
                                )?.label ?? account.sync_mode}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {account.institution_name || 'Unknown bank'} ·{' '}
                              {account.account_type_display}
                            </p>
                            {account.agent_sync_supported &&
                              account.agent_flow && (
                                <p className="text-xs text-muted-foreground">
                                  Agent flow:{' '}
                                  {agentFlowLabel(account.agent_flow)}
                                </p>
                              )}
                            {!account.agent_sync_supported && (
                              <p className="text-xs text-muted-foreground">
                                Playwright automation is not available for this
                                bank yet.
                              </p>
                            )}
                          </div>

                          <div className="w-full lg:w-56">
                            <Select
                              value={account.sync_mode}
                              disabled={isSaving}
                              onValueChange={value =>
                                void handleSyncModeChange(
                                  account,
                                  value as SyncMode
                                )
                              }
                            >
                              <SelectTrigger
                                aria-label={`Sync mode for ${account.name}`}
                              >
                                {isSaving ? (
                                  <span className="flex items-center gap-2">
                                    <LoadingSpinner className="h-4 w-4" />
                                    Saving...
                                  </span>
                                ) : (
                                  <SelectValue />
                                )}
                              </SelectTrigger>
                              <SelectContent>
                                {SYNC_MODE_OPTIONS.map(option => (
                                  <SelectItem
                                    key={option.value}
                                    value={option.value}
                                    disabled={
                                      option.value === 'auto' && autoDisabled
                                    }
                                  >
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        {needsAttention && (
                          <div className="mt-3 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                            <p>
                              Auto sync needs a Google Drive folder for this
                              account. Activate Drive in{' '}
                              <Link
                                to="/setup?tab=statements"
                                className="font-medium underline underline-offset-2"
                              >
                                Setup → Statements
                              </Link>{' '}
                              and sync missing folders.
                            </p>
                          </div>
                        )}

                        {account.sync_mode === 'auto' &&
                          account.agent_flow === 'investment_balance' &&
                          account.has_storage_uri && (
                            <div className="mt-3 flex items-start gap-2 text-xs text-muted-foreground">
                              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                              <p>
                                Balance scrape only — Google Drive folder is
                                optional for this account.
                              </p>
                            </div>
                          )}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5" />
            Host Agent Credentials
          </CardTitle>
          <CardDescription>
            Download or copy your API token and Fernet key for the host
            bank-agent. Treat them like passwords and do not share them.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-border bg-muted/20 p-4 space-y-4">
            <p className="text-sm text-muted-foreground">
              Save as{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                {AGENT_ENV_FILENAME}
              </code>{' '}
              in your repo root, then run{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                set -a && source {AGENT_ENV_FILENAME} && set +a
              </code>{' '}
              before{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                sync-config
              </code>
              .
            </p>
            <p className="text-xs text-muted-foreground">
              If you already configured the bank-agent with a different{' '}
              <code className="rounded bg-muted px-1 py-0.5">BANK_AGENT_FERNET_KEY</code>{' '}
              in your local <code className="rounded bg-muted px-1 py-0.5">.env</code>,
              keep using that key so saved bank logins stay decryptable.
            </p>

            <div className="space-y-3">
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">
                  RICHTATO_API_TOKEN
                </p>
                <code className="block truncate rounded-md border border-border bg-background px-3 py-2 font-mono text-xs">
                  {credentialsLoading
                    ? 'Loading...'
                    : credentialsVisible && credentials
                      ? credentials.token
                      : credentials
                        ? maskSecret(credentials.token)
                        : 'Reveal, copy, or download to load'}
                </code>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">
                  BANK_AGENT_FERNET_KEY
                </p>
                <code className="block truncate rounded-md border border-border bg-background px-3 py-2 font-mono text-xs">
                  {credentialsLoading
                    ? 'Loading...'
                    : credentialsVisible && credentials
                      ? credentials.fernetKey
                      : credentials
                        ? maskSecret(credentials.fernetKey)
                        : 'Reveal, copy, or download to load'}
                </code>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void handleRevealCredentials()}
                disabled={credentialsLoading}
              >
                {credentialsVisible ? (
                  <EyeOff className="mr-2 h-4 w-4" />
                ) : (
                  <Eye className="mr-2 h-4 w-4" />
                )}
                {credentialsVisible ? 'Hide' : 'Reveal'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void handleCopyCredentials()}
                disabled={credentialsLoading}
              >
                <Copy className="mr-2 h-4 w-4" />
                Copy .env
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => void handleDownloadCredentials()}
                disabled={credentialsLoading}
              >
                <Download className="mr-2 h-4 w-4" />
                Download .env
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Host Agent Setup
          </CardTitle>
          <CardDescription>
            Run these commands on your Linux desktop from the repo root after
            setting sync mode to Auto. The agent is not part of Docker Compose.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="rounded-lg border border-border bg-muted/30 p-4 font-mono text-xs leading-6 text-foreground">
            {HOST_COMMANDS.map(command => (
              <div key={command}>{command}</div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            Use{' '}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              ./scripts/bank_sync/start-headed.sh
            </code>{' '}
            to run the scheduled daemon after your first sign-in.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
