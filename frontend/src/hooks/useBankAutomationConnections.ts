/**
 * Hook for the Accounts page to load bank-automation connections and produce a
 * per-account lookup. Each Richtato account that is bound via a
 * `BankAccountLink` gets a `{ link, connection }` entry; unbound accounts are
 * absent from the map.
 *
 * Exposes a `refresh()` callback so child components can re-fetch after they
 * mutate a connection or account link (run, pause, toggle, etc.).
 */
import {
  bankAutomationApi,
  type BankAutomationAccountLink,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { useCallback, useEffect, useMemo, useState } from 'react';

export interface AccountSyncSummary {
  link: BankAutomationAccountLink;
  connection: BankAutomationConnection;
}

export type AccountSyncMap = Map<number, AccountSyncSummary>;

export interface UseBankAutomationConnectionsResult {
  connections: BankAutomationConnection[];
  byAccount: AccountSyncMap;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useBankAutomationConnections(): UseBankAutomationConnectionsResult {
  const [connections, setConnections] = useState<BankAutomationConnection[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const list = await bankAutomationApi.listConnections();
      setConnections(list);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load bank connections'
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
    for (const connection of connections) {
      for (const link of connection.account_links) {
        if (link.financial_account != null) {
          map.set(link.financial_account, { link, connection });
        }
      }
    }
    return map;
  }, [connections]);

  return { connections, byAccount, loading, error, refresh };
}
