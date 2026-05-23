/**
 * Connect-bank wizard.
 *
 * Three-step dialog that drives the cookie-only Playwright agent flow.
 * The user never types a bank URL, API token, or password into Richtato
 * — sign-in happens in a headed Chromium window the agent pops on the
 * host desktop.
 *
 * Step 1: Pick a supported institution.
 * Step 2: Confirm cadence/nickname; we create the BankLogin and queue an
 *         `interactive_login` task. The user watches their host desktop
 *         for the Chromium window, signs in there, and the agent posts
 *         cookies + discovered accounts back. We poll `/logins/{id}/`
 *         every few seconds until status flips to `active`.
 * Step 3: Bind the auto-discovered bank accounts to existing Richtato
 *         accounts. Users can skip an account or create the Richtato
 *         account out-of-band first.
 */
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  bankSyncApi,
  type BankLogin,
  type BankSyncCadence,
  type BindableAccount,
  type BulkBindRow,
  type SupportedInstitution,
  type SyncedAccount,
} from '@/lib/api/bankSync';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  ChevronRight,
  Globe,
  Loader2,
  MonitorPlay,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

interface ConnectBankWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called when the user closes the wizard after at least one bind succeeded. */
  onConnected: () => void | Promise<void>;
}

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;

type WizardStep = 'institution' | 'wait_for_login' | 'bind_accounts' | 'done';

const CADENCES: { value: BankSyncCadence; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'manual', label: 'Manual only' },
];

export function ConnectBankWizard({
  open,
  onOpenChange,
  onConnected,
}: ConnectBankWizardProps) {
  const [step, setStep] = useState<WizardStep>('institution');
  const [supported, setSupported] = useState<SupportedInstitution[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string>('');
  const [nickname, setNickname] = useState('');
  const [cadence, setCadence] = useState<BankSyncCadence>('daily');
  const [creating, setCreating] = useState(false);
  const [login, setLogin] = useState<BankLogin | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollExpired, setPollExpired] = useState(false);
  const [bindable, setBindable] = useState<BindableAccount[]>([]);
  const [bindings, setBindings] = useState<Record<string, number | ''>>({});
  const [binding, setBinding] = useState(false);

  const resetAll = useCallback(() => {
    setStep('institution');
    setSupported([]);
    setSelectedSlug('');
    setNickname('');
    setCadence('daily');
    setCreating(false);
    setLogin(null);
    setError(null);
    setPollExpired(false);
    setBindable([]);
    setBindings({});
    setBinding(false);
  }, []);

  useEffect(() => {
    if (!open) {
      resetAll();
      return;
    }
    const load = async () => {
      try {
        const inst = await bankSyncApi.listSupportedInstitutions();
        setSupported(inst);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load supported institutions'
        );
      }
    };
    void load();
  }, [open, resetAll]);

  useEffect(() => {
    if (step !== 'wait_for_login' || !login) return;
    let cancelled = false;
    const start = Date.now();

    const tick = async () => {
      if (cancelled) return;
      try {
        const fresh = await bankSyncApi.getLogin(login.id);
        if (cancelled) return;
        if (fresh.status === 'active') {
          setLogin(fresh);
          // Move into binding step. Pre-fill bindings using the discovered
          // detected_account_name + the bindable list filtered by slug.
          const candidates = await bankSyncApi.listBindableAccounts(
            fresh.institution_slug
          );
          setBindable(candidates);
          // Pre-pick the first matching Richtato account for each discovered
          // SyncedAccount that already has a token but no FK match yet.
          const next: Record<string, number | ''> = {};
          for (const synced of fresh.synced_accounts || []) {
            next[String(synced.id)] = synced.financial_account;
          }
          setBindings(next);
          setStep('bind_accounts');
          return;
        }
        if (fresh.status === 'error') {
          setError(fresh.last_failure_reason || 'Sign-in failed.');
          return;
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to poll for login'
          );
        }
      }
      if (Date.now() - start > POLL_TIMEOUT_MS) {
        setPollExpired(true);
        return;
      }
    };

    const timer = setInterval(tick, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [step, login]);

  const handleCreate = async () => {
    if (!selectedSlug) return;
    const institution = supported.find(s => s.slug === selectedSlug);
    if (!institution || institution.id === null) {
      setError(
        `Institution "${selectedSlug}" has not been seeded yet. Add it via the Django admin first.`
      );
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const created = await bankSyncApi.createLogin({
        institution: institution.id,
        nickname: nickname.trim() || institution.name,
        cadence,
        preferred_run_hour_local: 6,
      });
      await bankSyncApi.beginLogin(created.id);
      setLogin(created);
      setStep('wait_for_login');
      toast.info('Watch your desktop', {
        description:
          'A real Chromium window should pop up for you to sign in to your bank.',
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to start the sign-in flow.'
      );
    } finally {
      setCreating(false);
    }
  };

  const handleRetryBeginLogin = async () => {
    if (!login) return;
    setPollExpired(false);
    setError(null);
    try {
      await bankSyncApi.beginLogin(login.id);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to re-queue the sign-in task.'
      );
    }
  };

  const handleBindCommit = async () => {
    if (!login) return;
    setBinding(true);
    setError(null);
    try {
      const rows: BulkBindRow[] = [];
      const discovered = login.synced_accounts || [];
      for (const synced of discovered) {
        const choice = bindings[String(synced.id)];
        if (!choice) continue;
        if (choice === synced.financial_account) continue;
        rows.push({
          bank_login: login.id,
          financial_account: Number(choice),
          flow: synced.flow,
          external_account_token: synced.external_account_token,
          detected_account_name: synced.detected_account_name,
        });
      }
      if (rows.length > 0) {
        await bankSyncApi.bulkBind(rows);
      }
      setStep('done');
      await onConnected();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to bind accounts. Try again.'
      );
    } finally {
      setBinding(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" /> Connect a bank
          </DialogTitle>
          <DialogDescription>
            Sign-in always happens in a real browser window on your desktop.
            Richtato only stores the resulting cookies (encrypted) so it can
            download statements headless. Your bank password is never sent to
            us.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {step === 'institution' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Bank</Label>
              <div className="grid gap-2">
                {supported.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Loading supported banks…
                  </p>
                ) : (
                  supported.map(inst => (
                    <button
                      key={inst.slug}
                      type="button"
                      onClick={() => setSelectedSlug(inst.slug)}
                      className={cn(
                        'flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition hover:bg-muted/60',
                        selectedSlug === inst.slug
                          ? 'border-primary bg-primary/5'
                          : 'border-border'
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{inst.name}</span>
                      </span>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="nickname">Nickname</Label>
                <Input
                  id="nickname"
                  placeholder="e.g. BoFA (Personal)"
                  value={nickname}
                  onChange={e => setNickname(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Cadence</Label>
                <Select
                  value={cadence}
                  onValueChange={v => setCadence(v as BankSyncCadence)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CADENCES.map(c => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        )}

        {step === 'wait_for_login' && login && (
          <div className="space-y-4">
            <div className="flex items-start gap-3 rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
              <MonitorPlay className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
              <div>
                <p className="font-medium text-foreground">
                  Sign in to {login.institution_name} in the browser window
                </p>
                <p className="text-muted-foreground">
                  A real Chromium window should have opened on your desktop.
                  Complete sign-in (including any MFA), let your bank's
                  dashboard finish loading, then leave the window — we'll
                  capture cookies automatically.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Waiting for the agent to confirm sign-in…
            </div>
            {pollExpired && (
              <div className="flex items-center justify-between gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
                <span className="inline-flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Stopped waiting after 10 minutes. Want to try again?
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRetryBeginLogin}
                >
                  Retry
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'bind_accounts' && login && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Match each detected bank account to a Richtato account. Skip
              anything you don't want auto-synced.
            </p>
            {(login.synced_accounts || []).length === 0 ? (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                We didn't auto-discover any accounts. You can add them later by
                clicking Connect on each Richtato account.
              </div>
            ) : (
              <div className="space-y-2">
                {(login.synced_accounts || []).map(synced => (
                  <BindRow
                    key={synced.id}
                    synced={synced}
                    candidates={bindable}
                    value={bindings[String(synced.id)] ?? ''}
                    onChange={v =>
                      setBindings(prev => ({ ...prev, [String(synced.id)]: v }))
                    }
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {step === 'done' && (
          <div className="flex items-center gap-2 rounded-md border border-emerald-500/40 bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" />
            Connected. The agent will sync on its schedule (or use Sync now on
            the account).
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-2">
          {step === 'institution' && (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={creating}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!selectedSlug || creating}
                className="gap-2"
              >
                {creating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <MonitorPlay className="h-4 w-4" />
                )}
                Open browser to sign in
              </Button>
            </>
          )}
          {step === 'wait_for_login' && (
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close (we'll keep the login pending)
            </Button>
          )}
          {step === 'bind_accounts' && (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={binding}
              >
                Skip for now
              </Button>
              <Button onClick={handleBindCommit} disabled={binding}>
                {binding ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Save bindings
              </Button>
            </>
          )}
          {step === 'done' && (
            <Button onClick={() => onOpenChange(false)}>Done</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface BindRowProps {
  synced: SyncedAccount;
  candidates: BindableAccount[];
  value: number | '';
  onChange: (value: number | '') => void;
}

function BindRow({ synced, candidates, value, onChange }: BindRowProps) {
  const matching = candidates.filter(
    c => c.flow === synced.flow && !c.already_bound
  );
  return (
    <div className="grid items-center gap-3 rounded-md border border-border bg-muted/20 p-3 sm:grid-cols-[1fr_auto_1fr]">
      <div>
        <div className="text-sm font-medium text-foreground">
          {synced.detected_account_name || 'Unnamed account'}
        </div>
        <div className="text-xs text-muted-foreground">
          {synced.flow === 'credit_card' ? 'Credit card' : 'Deposit'}
        </div>
      </div>
      <ChevronRight className="hidden h-4 w-4 text-muted-foreground sm:block" />
      <div>
        <Select
          value={value === '' ? '' : String(value)}
          onValueChange={v => onChange(v === '' ? '' : Number(v))}
        >
          <SelectTrigger>
            <SelectValue placeholder="Pick a Richtato account…" />
          </SelectTrigger>
          <SelectContent>
            {matching.length === 0 ? (
              <div className="p-2 text-xs text-muted-foreground">
                No matching Richtato account. Create one on the Accounts page
                first.
              </div>
            ) : (
              matching.map(c => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.name}
                  {c.account_number_last4
                    ? ` ····${c.account_number_last4}`
                    : ''}
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
