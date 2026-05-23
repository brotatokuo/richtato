/**
 * Hook for the small "needs sign-in" badge in the sidebar.
 *
 * Polls the bank-sync login list every few minutes (cheap call; no
 * decrypted secrets) and surfaces a count of logins that need the user to
 * sign in again so the agent can refresh cookies.
 */
import { bankSyncApi, type BankLogin } from '@/lib/api/bankSync';
import { useEffect, useRef, useState } from 'react';

const REFRESH_INTERVAL_MS = 60_000 * 5;

export interface BankSyncStatusSummary {
  reauthCount: number;
  errorCount: number;
  pendingLoginCount: number;
  activeCount: number;
  loading: boolean;
}

export function useBankSyncStatus(): BankSyncStatusSummary {
  const [status, setStatus] = useState<BankSyncStatusSummary>({
    reauthCount: 0,
    errorCount: 0,
    pendingLoginCount: 0,
    activeCount: 0,
    loading: true,
  });
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const reduce = (logins: BankLogin[]) => {
      setStatus({
        reauthCount: logins.filter(l => l.status === 'needs_reauth').length,
        errorCount: logins.filter(l => l.status === 'error').length,
        pendingLoginCount: logins.filter(l => l.status === 'pending_login')
          .length,
        activeCount: logins.filter(l => l.status === 'active').length,
        loading: false,
      });
    };

    const refresh = async () => {
      try {
        const list = await bankSyncApi.listLogins();
        reduce(list);
      } catch {
        setStatus(prev => ({ ...prev, loading: false }));
      }
    };

    void refresh();
    timer.current = setInterval(() => {
      void refresh();
    }, REFRESH_INTERVAL_MS);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  return status;
}
