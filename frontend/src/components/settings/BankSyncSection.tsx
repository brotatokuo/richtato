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
import { Input } from '@/components/ui/input';
import {
  AGENT_CADENCE_OPTIONS,
  AGENT_HOUR_OPTIONS,
  agentFlowLabel,
  bankSyncApi,
  SYNC_MODE_OPTIONS,
  type AgentCadence,
  type BankSyncSetupAccount,
  type SyncMode,
} from '@/lib/api/bankSync';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Download,
  ExternalLink,
  Landmark,
  Loader2,
  RefreshCw,
  Terminal,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const HOST_COMMANDS = [
  'richtato bank setup',
  'richtato bank status',
  'richtato bank signin <login_id>',
  'richtato bank sync <login_id>',
  'richtato bank daemon',
] as const;

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

function accountNeedsStorage(account: BankSyncSetupAccount): boolean {
  return (
    account.sync_mode === 'auto' &&
    account.needs_storage_for_auto &&
    !account.has_storage_uri
  );
}

function accountNeedsActivityUrl(account: BankSyncSetupAccount): boolean {
  return account.needs_activity_url_for_auto && !account.has_activity_url;
}

function accountNeedsAttention(account: BankSyncSetupAccount): boolean {
  return accountNeedsStorage(account) || accountNeedsActivityUrl(account);
}

function activityUrlHelpText(account: BankSyncSetupAccount): string {
  if (account.institution_slug === 'bofa') {
    return 'Paste the Bank of America activity URL for this account. It should include adx=.';
  }
  if (account.institution_slug === 'chase') {
    return 'Paste the Chase account activity or transactions page URL for this account.';
  }
  if (account.institution_slug === 'guideline') {
    return 'Paste the Guideline 401(k) account page URL used for the balance scrape.';
  }
  return 'Paste the signed-in bank account activity URL used by the host bank-agent.';
}

export function BankSyncSection() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloadingSetup, setDownloadingSetup] = useState(false);
  const [accounts, setAccounts] = useState<BankSyncSetupAccount[]>([]);
  const [agentLoginCount, setAgentLoginCount] = useState(0);
  const [agentAccountCount, setAgentAccountCount] = useState(0);
  const [duplicateInstitutionLogins, setDuplicateInstitutionLogins] = useState<
    string[]
  >([]);
  const [savingAccountId, setSavingAccountId] = useState<number | null>(null);

  const loadSetup = useCallback(async (options?: { silent?: boolean }) => {
    if (options?.silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const payload = await bankSyncApi.getSetup();
      setAccounts(payload.accounts);
      setDuplicateInstitutionLogins(payload.duplicate_institution_logins);
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

  const missingStorageCount = useMemo(
    () => accounts.filter(accountNeedsStorage).length,
    [accounts]
  );
  const missingActivityUrlCount = useMemo(
    () => accounts.filter(accountNeedsActivityUrl).length,
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

  const handleScheduleChange = async (
    account: BankSyncSetupAccount,
    input: { agent_cadence?: AgentCadence; agent_sync_hour?: number }
  ) => {
    const nextCadence = input.agent_cadence ?? account.agent_cadence;
    const nextHour = input.agent_sync_hour ?? account.agent_sync_hour;
    if (
      nextCadence === account.agent_cadence &&
      nextHour === account.agent_sync_hour
    ) {
      return;
    }

    setSavingAccountId(account.id);
    try {
      await bankSyncApi.updateAccountSchedule(account.id, {
        agent_cadence: nextCadence,
        agent_sync_hour: nextHour,
      });
      toast.success(`${account.name} sync schedule updated`);
      await loadSetup({ silent: true });
    } catch (error) {
      toast.error('Unable to update sync schedule', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setSavingAccountId(null);
    }
  };

  const handleDownloadSetup = async () => {
    setDownloadingSetup(true);
    try {
      await bankSyncApi.downloadSetupYaml();
      toast.success('Downloaded richtato-bank-agent-setup.yml');
    } catch (error) {
      toast.error('Unable to download bank-agent setup', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setDownloadingSetup(false);
    }
  };

  const handleActivityUrlBlur = async (
    account: BankSyncSetupAccount,
    nextUrl: string
  ) => {
    const trimmedUrl = nextUrl.trim();
    if (trimmedUrl === account.activity_url) return;

    setSavingAccountId(account.id);
    try {
      await bankSyncApi.updateActivityUrl(account.id, trimmedUrl);
      toast.success(`${account.name} activity URL updated`);
      await loadSetup({ silent: true });
    } catch (error) {
      toast.error('Unable to update activity URL', {
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
            Set sync mode and schedule per account, then download one setup file
            for the host Playwright bank-agent on your desktop.
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
                    {agentLoginCount === 1 ? '' : 's'} in setup file
                  </Badge>
                  {missingStorageCount > 0 && (
                    <Badge variant="destructive">
                      {missingStorageCount} need
                      {missingStorageCount === 1 ? 's' : ''} Google Drive folder
                    </Badge>
                  )}
                  {missingActivityUrlCount > 0 && (
                    <Badge variant="destructive">
                      {missingActivityUrlCount} need
                      {missingActivityUrlCount === 1 ? 's' : ''} activity URL
                    </Badge>
                  )}
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Statement-based banks need Google Drive in{' '}
                  <Link
                    to="/setup?tab=statements"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Setup → Statements
                  </Link>
                  . Investment balance banks (Guideline, Robinhood) do not need
                  Drive folders.
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Auto sync accounts also need a bank activity URL. The setup
                  YAML exports that URL into the host agent vault; treat it as
                  sensitive.
                </p>
                {duplicateInstitutionLogins.length > 0 && (
                  <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                    Different schedules for the same bank (
                    {duplicateInstitutionLogins.join(', ')}) create separate
                    login entries. Sign in once per entry.
                  </p>
                )}
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-medium">Accounts</h3>
                <div className="flex flex-wrap gap-2">
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
                  <Button
                    size="sm"
                    onClick={() => void handleDownloadSetup()}
                    disabled={downloadingSetup || agentAccountCount === 0}
                  >
                    {downloadingSetup ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    Download setup
                  </Button>
                </div>
              </div>

              {agentAccountCount === 0 && accounts.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  Set at least one account to Auto sync before downloading
                  setup.
                </p>
              )}

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
                    const needsActivityUrl = accountNeedsActivityUrl(account);
                    const autoDisabled = !account.agent_sync_supported;
                    const scheduleDisabled =
                      isSaving || account.sync_mode !== 'auto';

                    return (
                      <div
                        key={account.id}
                        className={cn(
                          'rounded-lg border border-border p-4',
                          needsAttention && 'border-amber-500/40 bg-amber-500/5'
                        )}
                      >
                        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
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
                          </div>

                          <div className="grid w-full gap-2 sm:grid-cols-3 xl:w-[32rem]">
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

                            <Select
                              value={account.agent_cadence}
                              disabled={scheduleDisabled}
                              onValueChange={value =>
                                void handleScheduleChange(account, {
                                  agent_cadence: value as AgentCadence,
                                })
                              }
                            >
                              <SelectTrigger
                                aria-label={`Sync cadence for ${account.name}`}
                              >
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {AGENT_CADENCE_OPTIONS.map(option => (
                                  <SelectItem
                                    key={option.value}
                                    value={option.value}
                                  >
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>

                            <Select
                              value={String(account.agent_sync_hour)}
                              disabled={scheduleDisabled}
                              onValueChange={value =>
                                void handleScheduleChange(account, {
                                  agent_sync_hour: Number(value),
                                })
                              }
                            >
                              <SelectTrigger
                                aria-label={`Sync hour for ${account.name}`}
                              >
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {AGENT_HOUR_OPTIONS.map(option => (
                                  <SelectItem
                                    key={option.value}
                                    value={String(option.value)}
                                  >
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        {account.sync_mode === 'auto' &&
                          account.agent_sync_supported && (
                            <div className="mt-4 space-y-2">
                              <label
                                htmlFor={`activity-url-${account.id}`}
                                className="text-xs font-medium text-muted-foreground"
                              >
                                Activity URL
                              </label>
                              <Input
                                id={`activity-url-${account.id}`}
                                type="url"
                                defaultValue={account.activity_url}
                                disabled={isSaving}
                                placeholder="https://..."
                                aria-label={`Activity URL for ${account.name}`}
                                onBlur={event =>
                                  void handleActivityUrlBlur(
                                    account,
                                    event.currentTarget.value
                                  )
                                }
                              />
                              <p className="text-xs text-muted-foreground">
                                {activityUrlHelpText(account)}
                              </p>
                            </div>
                          )}

                        {accountNeedsStorage(account) && (
                          <div className="mt-3 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                            <p>
                              Auto sync needs a Google Drive folder. Activate
                              Drive in{' '}
                              <Link
                                to="/setup?tab=statements"
                                className="font-medium underline underline-offset-2"
                              >
                                Setup → Statements
                              </Link>
                              .
                            </p>
                          </div>
                        )}

                        {needsActivityUrl && (
                          <div className="mt-3 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                            <p>
                              Auto sync needs an activity URL before the
                              exported setup file can make this account ready
                              for downloads.
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
                                optional.
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
            <Terminal className="h-5 w-5" />
            Host Agent Setup
          </CardTitle>
          <CardDescription>
            After downloading setup, run the guided CLI from your repo root on
            your Linux desktop. Do not commit the setup file — it contains
            secrets and bank activity URLs.
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
              richtato bank
            </code>{' '}
            for daily status, sign-in, sync, daemon, and log actions after your
            first setup.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
