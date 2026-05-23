/**
 * Hook for the small "needs reauth" badge in the sidebar.
 *
 * Polls the bank-automation connection list every few minutes (cheap call;
 * no decrypted secrets) and surfaces a count of connections that are
 * waiting for a fresh Chrome-extension capture.
 */
import {
  bankAutomationApi,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { useEffect, useRef, useState } from 'react';

const REFRESH_INTERVAL_MS = 60_000 * 5;

export interface BankAutomationStatus {
  reauthCount: number;
  errorCount: number;
  totalActive: number;
  loading: boolean;
}

export function useBankAutomationStatus(): BankAutomationStatus {
  const [status, setStatus] = useState<BankAutomationStatus>({
    reauthCount: 0,
    errorCount: 0,
    totalActive: 0,
    loading: true,
  });
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const reduce = (connections: BankAutomationConnection[]) => {
      const reauth = connections.filter(
        c => c.status === 'reauth_required'
      ).length;
      const errors = connections.filter(c => c.status === 'error').length;
      const active = connections.filter(c => c.status === 'active').length;
      setStatus({
        reauthCount: reauth,
        errorCount: errors,
        totalActive: active,
        loading: false,
      });
    };

    const refresh = async () => {
      try {
        const list = await bankAutomationApi.listConnections();
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
