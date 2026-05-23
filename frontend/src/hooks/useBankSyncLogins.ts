/**
 * Hook for the Accounts page to load bank-sync logins and produce a
 * per-`FinancialAccount` lookup. Each Richtato account that is bound via a
 * `SyncedAccount` gets a `{ syncedAccount, login }` entry; unbound accounts
 * are absent from the map.
 *
 * Exposes a `refresh()` callback so child components can re-fetch after
 * they mutate a login or synced account.
 */
import {
  bankSyncApi,
  type BankLogin,
  type SyncedAccount,
} from '@/lib/api/bankSync';
import { useCallback, useEffect, useMemo, useState } from 'react';

export interface AccountSyncSummary {
  syncedAccount: SyncedAccount;
  login: BankLogin;
}

export type AccountSyncMap = Map<number, AccountSyncSummary>;

export interface UseBankSyncLoginsResult {
  logins: BankLogin[];
  byAccount: AccountSyncMap;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useBankSyncLogins(): UseBankSyncLoginsResult {
  const [logins, setLogins] = useState<BankLogin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const list = await bankSyncApi.listLogins();
      setLogins(list);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load bank logins'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const byAccount = useMemo<AccountSyncMap>(() => {
    const map: AccountSyncMap = new Map();
    for (const login of logins) {
      for (const syncedAccount of login.synced_accounts || []) {
        map.set(syncedAccount.financial_account, { syncedAccount, login });
      }
    }
    return map;
  }, [logins]);

  return { logins, byAccount, loading, error, refresh };
}
