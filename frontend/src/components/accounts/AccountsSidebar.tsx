import { AccountCreateModal } from '@/components/accounts/AccountCreateModal';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePreferences } from '@/contexts/PreferencesContext';
import type { AccountSyncMap } from '@/hooks/useBankSyncLogins';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { formatCurrency } from '@/lib/format';
import { getEntityLogo } from '@/lib/imageMapping';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  ChevronRight,
  CreditCard,
  Landmark,
  PauseCircle,
  Plus,
  Wallet,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

export interface AccountWithBalance extends Account {
  balance: number;
  lastUpdated: string;
}

interface AccountGroup {
  label: string;
  type: string;
  accounts: AccountWithBalance[];
  total: number;
  isLiability: boolean;
}

interface AccountsSidebarProps {
  selectedAccountId: number | null;
  onAccountSelect: (account: AccountWithBalance) => void;
  onAccountsChange?: () => void;
  syncMap: AccountSyncMap;
}

function AccountIcon({ type }: { type: string }) {
  const t = (type || '').toLowerCase();
  if (t === 'credit_card' || t === 'credit')
    return <CreditCard className="h-4 w-4" />;
  if (t === 'savings' || t === 'savings_account')
    return <Wallet className="h-4 w-4" />;
  return <Building2 className="h-4 w-4" />;
}

const GROUP_ORDER = ['checking', 'savings', 'credit_card'];

function SyncIndicator({
  syncMap,
  accountId,
}: {
  syncMap: AccountSyncMap;
  accountId: number;
}) {
  const summary = syncMap.get(accountId);
  if (!summary) return null;
  const { login, syncedAccount } = summary;
  if (login.status === 'error') {
    return (
      <span title={`Sync error: ${login.last_failure_reason || 'unknown'}`}>
        <WifiOff className="h-3 w-3 text-red-500" />
      </span>
    );
  }
  if (login.status === 'needs_reauth') {
    return (
      <span title="Bank session needs sign-in">
        <AlertTriangle className="h-3 w-3 text-amber-500" />
      </span>
    );
  }
  if (login.status === 'disabled' || !syncedAccount.enabled) {
    return (
      <span
        title={
          login.status === 'disabled'
            ? 'Bank login paused'
            : 'Auto-sync off for this account'
        }
      >
        <PauseCircle className="h-3 w-3 text-muted-foreground" />
      </span>
    );
  }
  return (
    <span title="Auto-sync on">
      <Wifi className="h-3 w-3 text-emerald-500" />
    </span>
  );
}

export function AccountsSidebar({
  selectedAccountId,
  onAccountSelect,
  onAccountsChange,
  syncMap,
}: AccountsSidebarProps) {
  const { preferences } = usePreferences();
  const [accounts, setAccounts] = useState<AccountWithBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
    new Set()
  );
  const [showCreate, setShowCreate] = useState(false);
  const [accountTypeOptions, setAccountTypeOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [entityOptions, setEntityOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [creating, setCreating] = useState(false);

  const loadAccounts = useCallback(async () => {
    try {
      const data = await transactionsApiService.getAccounts();
      const withBalance: AccountWithBalance[] = data.map(a => {
        const raw = a as Account & { balance?: number | string; date?: string };
        return {
          ...a,
          balance:
            typeof raw.balance === 'number'
              ? raw.balance
              : Number(String(raw.balance || '0').replace(/[^0-9.-]+/g, '')),
          lastUpdated: String(raw.date || ''),
        };
      });
      setAccounts(withBalance);
    } catch {
      // silent — the page will handle errors
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
    transactionsApiService
      .getAccountFieldChoices()
      .then(c => {
        setAccountTypeOptions(c.type || []);
        setEntityOptions(c.entity || []);
      })
      .catch(() => {});
  }, [loadAccounts]);

  const groups = useMemo<AccountGroup[]>(() => {
    const map: Record<string, AccountWithBalance[]> = {};
    accounts.forEach(a => {
      const t = a.account_type || a.type || 'other';
      if (!map[t]) map[t] = [];
      map[t].push(a);
    });

    return Object.entries(map)
      .sort(([a], [b]) => {
        const ia = GROUP_ORDER.indexOf(a);
        const ib = GROUP_ORDER.indexOf(b);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      })
      .map(([type, accs]) => {
        const isLiability = type === 'credit_card';
        const total = accs.reduce((s, a) => s + a.balance, 0);
        const label =
          type === 'checking'
            ? 'Checking'
            : type === 'savings'
              ? 'Savings'
              : type === 'credit_card'
                ? 'Credit Cards'
                : 'Other';
        return { label, type, accounts: accs, total, isLiability };
      });
  }, [accounts]);

  const totalAssets = accounts
    .filter(a => (a.account_type || a.type) !== 'credit_card')
    .reduce((s, a) => s + a.balance, 0);

  const totalLiabilities = accounts
    .filter(a => (a.account_type || a.type) === 'credit_card')
    .reduce((s, a) => s + Math.abs(a.balance), 0);

  const netWorth = totalAssets - totalLiabilities;

  const toggleGroup = (type: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const handleCreate = async (form: {
    name: string;
    type: string;
    entity: string;
  }) => {
    setCreating(true);
    try {
      await transactionsApiService.createAccount({
        name: form.name,
        type: form.type,
        institution_slug: form.entity,
      });
      await loadAccounts();
      onAccountsChange?.();
      setShowCreate(false);
    } catch (e) {
      toast.error('Failed to create account', {
        description: e instanceof Error ? e.message : undefined,
      });
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Net Worth Header */}
      <div className="px-4 pt-4 pb-3 border-b border-border/60">
        <div className="mb-3">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            Net Worth
          </p>
          <p
            className={cn(
              'text-2xl font-bold tabular-nums',
              netWorth >= 0 ? 'text-foreground' : 'text-red-500'
            )}
          >
            {formatCurrency(netWorth, preferences.currency, 0)}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-green-500/8 px-2.5 py-1.5">
            <p className="text-xs text-muted-foreground">Assets</p>
            <p className="text-sm font-semibold text-green-600 tabular-nums">
              {formatCurrency(totalAssets, preferences.currency, 0)}
            </p>
          </div>
          <div className="rounded-lg bg-red-500/8 px-2.5 py-1.5">
            <p className="text-xs text-muted-foreground">Liabilities</p>
            <p className="text-sm font-semibold text-red-500 tabular-nums">
              {formatCurrency(totalLiabilities, preferences.currency, 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 px-4 py-2.5 border-b border-border/40">
        <Button
          size="sm"
          variant="outline"
          className="flex-1 h-8 text-xs"
          onClick={() => setShowCreate(true)}
        >
          <Plus className="h-3.5 w-3.5 mr-1" />
          Add Account
        </Button>
      </div>

      {/* Accounts grouped list */}
      <div className="flex-1 overflow-y-auto py-2">
        {accounts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-center px-4">
            <Landmark className="h-8 w-8 text-muted-foreground/40 mb-2" />
            <p className="text-sm text-muted-foreground">No accounts yet</p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Add an account to get started
            </p>
          </div>
        ) : (
          groups.map(group => {
            const isCollapsed = collapsedGroups.has(group.type);
            return (
              <div key={group.type} className="mb-1">
                {/* Group header */}
                <button
                  onClick={() => toggleGroup(group.type)}
                  className="w-full flex items-center justify-between px-4 py-1.5 hover:bg-muted/40 transition-colors group"
                >
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {isCollapsed ? (
                      <ChevronRight className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                    {group.label}
                    <span className="font-normal normal-case tracking-normal text-muted-foreground/60">
                      ({group.accounts.length})
                    </span>
                  </div>
                  <span
                    className={cn(
                      'text-xs font-semibold tabular-nums',
                      group.isLiability
                        ? 'text-red-500'
                        : 'text-muted-foreground'
                    )}
                  >
                    {group.isLiability ? '-' : ''}
                    {formatCurrency(
                      Math.abs(group.total),
                      preferences.currency,
                      0
                    )}
                  </span>
                </button>

                {/* Account rows */}
                {!isCollapsed && (
                  <div className="px-2">
                    {group.accounts.map(account => {
                      const isSelected = selectedAccountId === account.id;
                      const entityLogo = getEntityLogo(account.entity || '');

                      return (
                        <button
                          key={account.id}
                          onClick={() => onAccountSelect(account)}
                          className={cn(
                            'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all',
                            isSelected
                              ? 'bg-primary/10 ring-1 ring-primary/40'
                              : 'hover:bg-muted/50'
                          )}
                        >
                          {/* Institution logo or icon */}
                          <div
                            className={cn(
                              'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center overflow-hidden',
                              isSelected ? 'bg-primary/15' : 'bg-muted'
                            )}
                          >
                            {entityLogo ? (
                              <img
                                src={entityLogo}
                                alt={account.institution_name || ''}
                                className="w-5 h-5 object-contain"
                              />
                            ) : (
                              <span
                                className={cn(
                                  'text-muted-foreground',
                                  isSelected && 'text-primary'
                                )}
                              >
                                <AccountIcon
                                  type={
                                    account.account_type || account.type || ''
                                  }
                                />
                              </span>
                            )}
                          </div>

                          {/* Name + masked number */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span
                                className={cn(
                                  'text-sm font-medium truncate',
                                  isSelected
                                    ? 'text-primary'
                                    : 'text-foreground'
                                )}
                              >
                                {account.name}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              {account.account_number_last4 && (
                                <span className="text-xs text-muted-foreground/70 font-mono">
                                  ····{account.account_number_last4}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Balance + sync dot */}
                          <div className="flex-shrink-0 flex flex-col items-end gap-1">
                            <span
                              className={cn(
                                'text-sm font-semibold tabular-nums',
                                group.isLiability
                                  ? 'text-red-500'
                                  : 'text-foreground'
                              )}
                            >
                              {group.isLiability && account.balance < 0
                                ? ''
                                : group.isLiability
                                  ? '-'
                                  : ''}
                              {formatCurrency(
                                Math.abs(account.balance),
                                preferences.currency,
                                0
                              )}
                            </span>
                            <SyncIndicator
                              syncMap={syncMap}
                              accountId={account.id}
                            />
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Create modal */}
      <AccountCreateModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={creating}
      />
    </div>
  );
}
