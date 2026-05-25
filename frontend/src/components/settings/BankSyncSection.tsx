import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
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
import {
  bankAgentLocalApi,
  getStoredLocalAgentConnection,
  storeLocalAgentConnection,
  type LocalAgentLogin,
  type LocalAgentStatus,
} from '@/lib/api/bankAgentLocal';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  Circle,
  Clock,
  Download,
  ExternalLink,
  Landmark,
  Loader2,
  PlugZap,
  RefreshCw,
  Terminal,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const HOST_COMMANDS = [
  'richtato bank setup',
  'richtato bank status',
  'richtato bank signin <login_id>',
  'richtato bank sync <login_id>',
  'BANK_AGENT_LOCAL_TOKEN=<token> richtato bank api',
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

function scheduleLabel(account: BankSyncSetupAccount): string {
  const cadence =
    AGENT_CADENCE_OPTIONS.find(o => o.value === account.agent_cadence)?.label ??
    account.agent_cadence;
  const hour = String(account.agent_sync_hour).padStart(2, '0') + ':00';
  return `${cadence} · ${hour}`;
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

function localLoginHasValidSession(login: LocalAgentLogin): boolean {
  return login.status === 'active' && Boolean(login.cookies_captured_at);
}

function localLoginStatusLabel(login: LocalAgentLogin): string {
  if (localLoginHasValidSession(login)) {
    return 'Logged in';
  }
  switch (login.status) {
    case 'needs_reauth':
      return 'Needs re-login';
    case 'pending_login':
      return 'Not signed in';
    case 'active':
      return 'Not signed in';
    case 'disabled':
      return 'Disabled';
    case 'error':
      return 'Error';
    default:
      return login.status.replaceAll('_', ' ');
  }
}

function localLoginSignInLabel(login: LocalAgentLogin): string {
  if (localLoginHasValidSession(login)) {
    return 'Refresh sign-in';
  }
  return login.status === 'needs_reauth' ? 'Re-login' : 'Sign in';
}

// ── Account row ────────────────────────────────────────────────────────────────

interface AccountRowProps {
  account: BankSyncSetupAccount;
  isSaving: boolean;
  onSyncModeChange: (account: BankSyncSetupAccount, mode: SyncMode) => void;
  onScheduleChange: (
    account: BankSyncSetupAccount,
    input: { agent_cadence?: AgentCadence; agent_sync_hour?: number }
  ) => void;
  onActivityUrlBlur: (account: BankSyncSetupAccount, url: string) => void;
}

function AccountRow({
  account,
  isSaving,
  onSyncModeChange,
  onScheduleChange,
  onActivityUrlBlur,
}: AccountRowProps) {
  const isAuto = account.sync_mode === 'auto';
  const needsAttention = accountNeedsAttention(account);
  const needsActivityUrl = accountNeedsActivityUrl(account);
  const autoDisabled = !account.agent_sync_supported;

  // Auto-expand rows that need attention so the user sees what's missing.
  const [expanded, setExpanded] = useState(needsAttention && isAuto);

  return (
    <div
      className={cn(
        'rounded-lg border border-border',
        needsAttention && 'border-amber-500/40 bg-amber-500/5'
      )}
    >
      {/* Compact header row */}
      <div className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1 space-y-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium">{account.name}</p>
            <Badge variant={syncModeBadgeVariant(account.sync_mode)}>
              {SYNC_MODE_OPTIONS.find(o => o.value === account.sync_mode)
                ?.label ?? account.sync_mode}
            </Badge>
            {needsAttention && (
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
            )}
          </div>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
            <span>
              {account.institution_name || 'Unknown bank'} ·{' '}
              {account.account_type_display}
            </span>
            {isAuto && account.agent_cadence !== 'manual' && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {scheduleLabel(account)}
              </span>
            )}
            {isAuto && account.agent_cadence === 'manual' && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                On demand
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Select
            value={account.sync_mode}
            disabled={isSaving}
            onValueChange={value =>
              onSyncModeChange(account, value as SyncMode)
            }
          >
            <SelectTrigger
              className="w-36"
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
                  disabled={option.value === 'auto' && autoDisabled}
                >
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Only show expand toggle for auto accounts */}
          {isAuto && (
            <button
              onClick={() => setExpanded(v => !v)}
              aria-label={expanded ? 'Collapse details' : 'Expand details'}
              className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <ChevronDown
                className={cn(
                  'h-4 w-4 transition-transform',
                  expanded && 'rotate-180'
                )}
              />
            </button>
          )}
        </div>
      </div>

      {/* Expandable details — auto accounts only */}
      {isAuto && expanded && (
        <div className="border-t border-border px-3 pb-3 pt-3 space-y-4">
          {/* Schedule */}
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-muted-foreground">
              Schedule
            </p>
            <div className="grid grid-cols-2 gap-2 sm:w-72">
              <Select
                value={account.agent_cadence}
                disabled={isSaving}
                onValueChange={value =>
                  onScheduleChange(account, {
                    agent_cadence: value as AgentCadence,
                  })
                }
              >
                <SelectTrigger aria-label={`Sync cadence for ${account.name}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_CADENCE_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={String(account.agent_sync_hour)}
                disabled={isSaving}
                onValueChange={value =>
                  onScheduleChange(account, {
                    agent_sync_hour: Number(value),
                  })
                }
              >
                <SelectTrigger aria-label={`Sync hour for ${account.name}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_HOUR_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Agent flow */}
          {account.agent_sync_supported && account.agent_flow && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {account.agent_flow === 'investment_balance' ? (
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
              ) : (
                <Bot className="h-3.5 w-3.5 shrink-0" />
              )}
              <span>{agentFlowLabel(account.agent_flow)}</span>
              {account.agent_flow === 'investment_balance' && (
                <span className="text-muted-foreground/70">
                  — Drive folder optional
                </span>
              )}
            </div>
          )}

          {/* Activity URL */}
          {account.agent_sync_supported && (
            <div className="space-y-1.5">
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
                  onActivityUrlBlur(account, event.currentTarget.value)
                }
              />
              <p className="text-xs text-muted-foreground">
                {activityUrlHelpText(account)}
              </p>
            </div>
          )}

          {/* Warnings */}
          {accountNeedsStorage(account) && (
            <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                Auto sync needs a Google Drive folder. Activate Drive in{' '}
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
            <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                Auto sync needs an activity URL before the exported setup file
                can make this account ready for downloads.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

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
  const [localBaseUrl, setLocalBaseUrl] = useState(
    () => getStoredLocalAgentConnection().baseUrl
  );
  const [localToken, setLocalToken] = useState(
    () => getStoredLocalAgentConnection().token
  );
  const [localStatus, setLocalStatus] = useState<LocalAgentStatus | null>(null);
  const [localAgentError, setLocalAgentError] = useState<string | null>(null);
  const [checkingLocalAgent, setCheckingLocalAgent] = useState(false);
  const [applyingSetup, setApplyingSetup] = useState(false);
  const [localActionLoginId, setLocalActionLoginId] = useState<number | null>(
    null
  );
  const [connectionExpanded, setConnectionExpanded] = useState(false);
  const [cliExpanded, setCliExpanded] = useState(false);

  const autoConnectAttempted = useRef(false);

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

  const handleCheckLocalAgent = useCallback(
    async (opts?: { silent?: boolean }) => {
      setCheckingLocalAgent(true);
      if (!opts?.silent) setLocalAgentError(null);
      try {
        storeLocalAgentConnection({ baseUrl: localBaseUrl, token: localToken });
        const status = await bankAgentLocalApi.getStatus({
          baseUrl: localBaseUrl,
          token: localToken,
        });
        setLocalStatus(status);
        setLocalAgentError(null);
        if (!opts?.silent) toast.success('Connected to local bank-agent');
      } catch (error) {
        setLocalStatus(null);
        const message =
          error instanceof Error
            ? error.message
            : 'Unable to reach local agent.';
        setLocalAgentError(message);
        if (!opts?.silent)
          toast.error('Local bank-agent unavailable', { description: message });
      } finally {
        setCheckingLocalAgent(false);
      }
    },
    [localBaseUrl, localToken]
  );

  useEffect(() => {
    void loadSetup();
  }, [loadSetup]);

  // Auto-connect on first mount when credentials are already stored.
  useEffect(() => {
    if (autoConnectAttempted.current) return;
    autoConnectAttempted.current = true;
    const stored = getStoredLocalAgentConnection();
    if (stored.baseUrl) {
      void handleCheckLocalAgent({ silent: true });
    }
  }, [handleCheckLocalAgent]);

  const missingStorageCount = useMemo(
    () => accounts.filter(accountNeedsStorage).length,
    [accounts]
  );
  const missingActivityUrlCount = useMemo(
    () => accounts.filter(accountNeedsActivityUrl).length,
    [accounts]
  );
  const attentionCount = missingStorageCount + missingActivityUrlCount;

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

  const handleApplySetupToLocalAgent = async () => {
    setApplyingSetup(true);
    setLocalAgentError(null);
    try {
      storeLocalAgentConnection({ baseUrl: localBaseUrl, token: localToken });
      const yaml = await bankSyncApi.getSetupYamlText();
      const result = await bankAgentLocalApi.applyYaml({
        baseUrl: localBaseUrl,
        token: localToken,
        yaml,
      });
      if (result.status) {
        setLocalStatus(result.status);
      }
      toast.success('Applied setup to local bank-agent');
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to apply setup.';
      setLocalAgentError(message);
      toast.error('Unable to apply setup', { description: message });
    } finally {
      setApplyingSetup(false);
    }
  };

  const handleLocalSignIn = async (loginId: number) => {
    setLocalActionLoginId(loginId);
    try {
      const result = await bankAgentLocalApi.signIn({
        baseUrl: localBaseUrl,
        token: localToken,
        loginId,
      });
      if (result.status) {
        setLocalStatus(result.status);
      }
      toast.success(result.message || 'Sign-in completed');
    } catch (error) {
      toast.error('Unable to start sign-in', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setLocalActionLoginId(null);
    }
  };

  const handleLocalSync = async (loginId: number) => {
    setLocalActionLoginId(loginId);
    try {
      const result = await bankAgentLocalApi.sync({
        baseUrl: localBaseUrl,
        token: localToken,
        loginId,
      });
      if (result.status) {
        setLocalStatus(result.status);
      }
      toast.success('Manual sync finished');
    } catch (error) {
      toast.error('Manual sync needs attention', {
        description:
          error instanceof Error ? error.message : 'Please check the agent.',
      });
      void handleCheckLocalAgent();
    } finally {
      setLocalActionLoginId(null);
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

  const handleDisconnect = () => {
    setLocalStatus(null);
    setLocalAgentError(null);
    setConnectionExpanded(true);
  };

  const isConnected = localStatus !== null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Bank Agent
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadSetup({ silent: true })}
            disabled={refreshing || loading}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* ── Accounts ──────────────────────────────────────────── */}
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading sync settings...
          </div>
        ) : (
          <>
            {/* Status summary */}
            {accounts.length > 0 && (
              <div
                className={cn(
                  'flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border px-3 py-2 text-sm',
                  attentionCount > 0
                    ? 'border-amber-500/40 bg-amber-500/5 text-amber-700 dark:text-amber-300'
                    : 'border-border bg-muted/20 text-muted-foreground'
                )}
              >
                {attentionCount > 0 ? (
                  <>
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>
                      {attentionCount} account
                      {attentionCount === 1 ? '' : 's'} need
                      {attentionCount === 1 ? 's' : ''} attention
                    </span>
                    {missingStorageCount > 0 && (
                      <span className="text-xs">
                        ·{' '}
                        <Link
                          to="/setup?tab=statements"
                          className="font-medium underline underline-offset-2"
                        >
                          {missingStorageCount} need
                          {missingStorageCount === 1 ? 's' : ''} Drive folder
                        </Link>
                      </span>
                    )}
                    {missingActivityUrlCount > 0 && (
                      <span className="text-xs">
                        · {missingActivityUrlCount} need
                        {missingActivityUrlCount === 1 ? 's' : ''} activity URL
                        — expand to add
                      </span>
                    )}
                  </>
                ) : agentAccountCount > 0 ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                    <span className="text-foreground">
                      {agentAccountCount} account
                      {agentAccountCount === 1 ? '' : 's'} syncing automatically
                    </span>
                    <span className="text-xs">
                      · {agentLoginCount} bank login
                      {agentLoginCount === 1 ? '' : 's'} in setup
                    </span>
                  </>
                ) : (
                  <span>No accounts set to auto sync yet.</span>
                )}
                {duplicateInstitutionLogins.length > 0 && (
                  <span className="text-xs text-amber-700 dark:text-amber-300">
                    · Different schedules for{' '}
                    {duplicateInstitutionLogins.join(', ')} create separate
                    logins — sign in once per entry.
                  </span>
                )}
              </div>
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
              <div className="space-y-2">
                {accounts.map(account => (
                  <AccountRow
                    key={account.id}
                    account={account}
                    isSaving={savingAccountId === account.id}
                    onSyncModeChange={handleSyncModeChange}
                    onScheduleChange={handleScheduleChange}
                    onActivityUrlBlur={handleActivityUrlBlur}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* ── Divider ───────────────────────────────────────────── */}
        <hr className="border-border" />

        {/* ── Agent ─────────────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Actions */}
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() => void handleDownloadSetup()}
              disabled={downloadingSetup || agentAccountCount === 0 || loading}
              variant="outline"
            >
              {downloadingSetup ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              Download setup YAML
            </Button>
            <Button
              onClick={() => void handleApplySetupToLocalAgent()}
              disabled={applyingSetup || agentAccountCount === 0 || loading}
            >
              {applyingSetup ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <PlugZap className="mr-2 h-4 w-4" />
              )}
              Apply to running agent
            </Button>
          </div>

          {agentAccountCount === 0 && accounts.length > 0 && !loading && (
            <p className="text-sm text-muted-foreground">
              Set at least one account to Auto sync to enable setup actions.
            </p>
          )}

          {/* Connection indicator */}
          <Collapsible
            open={connectionExpanded || !isConnected}
            onOpenChange={open => {
              if (isConnected) setConnectionExpanded(open);
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm">
                {checkingLocalAgent ? (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                ) : isConnected ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Circle className="h-4 w-4 text-muted-foreground" />
                )}
                <span
                  className={cn(
                    'font-medium',
                    isConnected
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-muted-foreground'
                  )}
                >
                  {checkingLocalAgent
                    ? 'Connecting…'
                    : isConnected
                      ? `Connected · ${localBaseUrl}`
                      : 'Not connected'}
                </span>
              </div>
              <div className="flex items-center gap-1">
                {isConnected && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void handleCheckLocalAgent()}
                      disabled={checkingLocalAgent}
                      className="h-7 px-2"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleDisconnect}
                      className="h-7 px-2 text-muted-foreground"
                      aria-label="Disconnect"
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </>
                )}
                {!isConnected && (
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-muted-foreground"
                    >
                      <ChevronDown
                        className={cn(
                          'h-3.5 w-3.5 transition-transform',
                          (connectionExpanded || !isConnected) && 'rotate-180'
                        )}
                      />
                    </Button>
                  </CollapsibleTrigger>
                )}
              </div>
            </div>

            <CollapsibleContent className="mt-3 space-y-3">
              <div className="grid gap-3 md:grid-cols-[1fr_14rem_auto]">
                <Input
                  value={localBaseUrl}
                  onChange={event => setLocalBaseUrl(event.currentTarget.value)}
                  aria-label="Local bank-agent URL"
                  placeholder="http://127.0.0.1:8765"
                />
                <Input
                  value={localToken}
                  onChange={event => setLocalToken(event.currentTarget.value)}
                  aria-label="Local bank-agent token"
                  placeholder="Optional local token"
                  type="password"
                />
                <Button
                  variant="outline"
                  onClick={() => void handleCheckLocalAgent()}
                  disabled={checkingLocalAgent}
                >
                  {checkingLocalAgent ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Connect
                </Button>
              </div>
              {localAgentError && (
                <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-300">
                  {localAgentError}
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Requires the agent running with{' '}
                <code className="rounded bg-muted px-1 py-0.5">
                  richtato bank api
                </code>
                . Status calls only expose schedule metadata — no cookies or
                activity URLs are sent.
              </p>
            </CollapsibleContent>
          </Collapsible>

          {/* Live login list */}
          {localStatus && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge variant="default">
                  {localStatus.login_count} local login
                  {localStatus.login_count === 1 ? '' : 's'}
                </Badge>
                <Badge variant="outline">
                  {localStatus.account_count} local account
                  {localStatus.account_count === 1 ? '' : 's'}
                </Badge>
                {localStatus.reauth_required && (
                  <Badge variant="destructive">Re-login required</Badge>
                )}
              </div>

              {localStatus.logins.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  The local agent vault is empty. Apply the current setup, then
                  sign in to each login.
                </p>
              ) : (
                <div className="space-y-2">
                  {localStatus.logins.map(login => {
                    const hasValidSession = localLoginHasValidSession(login);
                    return (
                      <div
                        key={login.id}
                        className={cn(
                          'rounded-lg border border-border p-3',
                          hasValidSession &&
                            'border-emerald-500/30 bg-emerald-500/5',
                          !hasValidSession &&
                            (login.status === 'needs_reauth' ||
                              login.status === 'pending_login') &&
                            'border-amber-500/40 bg-amber-500/5'
                        )}
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-medium">
                                #{login.id} {login.institution_slug}
                                {login.nickname ? ` / ${login.nickname}` : ''}
                              </p>
                              <Badge
                                variant={
                                  hasValidSession
                                    ? 'default'
                                    : login.status === 'needs_reauth' ||
                                        login.status === 'error'
                                      ? 'destructive'
                                      : 'secondary'
                                }
                              >
                                {localLoginStatusLabel(login)}
                              </Badge>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {login.accounts.length} account
                              {login.accounts.length === 1 ? '' : 's'} · last
                              success {login.last_success_at || 'never'} · next{' '}
                              {login.next_run_at || 'not scheduled'}
                              {login.cookies_captured_at
                                ? ` · cookies ${login.cookies_captured_at}`
                                : ''}
                            </p>
                            {login.last_failure_reason && (
                              <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                                {login.last_failure_reason}
                              </p>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {hasValidSession && (
                              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                                <CheckCircle2 className="h-4 w-4 shrink-0" />
                                Session ready
                              </div>
                            )}
                            <Button
                              size="sm"
                              variant={hasValidSession ? 'outline' : 'default'}
                              onClick={() => void handleLocalSignIn(login.id)}
                              disabled={localActionLoginId === login.id}
                            >
                              {localActionLoginId === login.id ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : null}
                              {localLoginSignInLabel(login)}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => void handleLocalSync(login.id)}
                              disabled={
                                localActionLoginId === login.id ||
                                !hasValidSession
                              }
                            >
                              Sync now
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* CLI reference — collapsed by default */}
          <Collapsible open={cliExpanded} onOpenChange={setCliExpanded}>
            <CollapsibleTrigger asChild>
              <button className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground">
                <Terminal className="h-3.5 w-3.5" />
                CLI commands
                <ChevronDown
                  className={cn(
                    'h-3.5 w-3.5 transition-transform',
                    cliExpanded && 'rotate-180'
                  )}
                />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-3 space-y-3">
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
                for daily status, sign-in, sync, daemon, and log actions after
                your first setup.
              </p>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </CardContent>
    </Card>
  );
}
