/**
 * Hook for polling bank sync status.
 *
 * This hook automatically polls for sync status and provides:
 * - Current sync state (is_syncing, new_transaction_count, last_sync)
 * - Method to clear the new transaction count
 * - Optional callback when sync completes
 *
 * The backend middleware automatically triggers sync when connections are stale,
 * so the frontend only needs to poll for status updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { syncService, SyncStatus } from '@/lib/api/sync';

interface UseSyncStatusOptions {
  /** Callback when sync completes (transitions from syncing to not syncing) */
  onSyncComplete?: (newTransactionCount: number) => void;
  /** Callback when sync fails */
  onSyncError?: (error: string) => void;
}

interface UseSyncStatusReturn {
  /** Current sync status, null if not yet fetched */
  status: SyncStatus | null;
  /** True if currently fetching status */
  isLoading: boolean;
  /** Clear the new transaction count (call when user views transactions) */
  clearNewCount: () => Promise<void>;
  /** Manually refresh the status */
  refresh: () => Promise<void>;
}

export function useSyncStatus(
  options: UseSyncStatusOptions = {}
): UseSyncStatusReturn {
  const { onSyncComplete, onSyncError } = options;
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Track previous syncing state to detect completion
  const wasSyncingRef = useRef(false);

  // Store callbacks in refs to avoid re-running effect when they change
  const onSyncCompleteRef = useRef(onSyncComplete);
  const onSyncErrorRef = useRef(onSyncError);

  // Keep refs up to date
  useEffect(() => {
    onSyncCompleteRef.current = onSyncComplete;
    onSyncErrorRef.current = onSyncError;
  }, [onSyncComplete, onSyncError]);

  const checkStatus = useCallback(async () => {
    try {
      const s = await syncService.getStatus();
      setStatus(s);
    } catch {
      // Ignore errors (user may not be authenticated)
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Poll status on mount and periodically while syncing
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    let isMounted = true;

    const startPolling = async () => {
      if (!isMounted) return;

      try {
        const s = await syncService.getStatus();
        if (!isMounted) return;

        // Detect sync completion (was syncing, now not syncing)
        if (wasSyncingRef.current && !s.is_syncing) {
          if (s.last_error) {
            onSyncErrorRef.current?.(s.last_error);
          } else {
            onSyncCompleteRef.current?.(s.new_transaction_count);
          }
        }
        wasSyncingRef.current = s.is_syncing;

        setStatus(s);
        setIsLoading(false);

        // If syncing, poll more frequently (every 3 seconds)
        if (s.is_syncing && !interval) {
          interval = setInterval(async () => {
            if (!isMounted) return;
            try {
              const newStatus = await syncService.getStatus();
              if (!isMounted) return;

              // Detect sync completion during polling
              if (wasSyncingRef.current && !newStatus.is_syncing) {
                if (newStatus.last_error) {
                  onSyncErrorRef.current?.(newStatus.last_error);
                } else {
                  onSyncCompleteRef.current?.(newStatus.new_transaction_count);
                }
              }
              wasSyncingRef.current = newStatus.is_syncing;

              setStatus(newStatus);

              // Stop polling when sync is complete
              if (!newStatus.is_syncing && interval) {
                clearInterval(interval);
                interval = null;
              }
            } catch {
              // Ignore polling errors
            }
          }, 3000);
        }
      } catch {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    startPolling();

    // Also check on window focus (user returns to tab)
    const handleFocus = () => {
      startPolling();
    };
    window.addEventListener('focus', handleFocus);

    return () => {
      isMounted = false;
      if (interval) clearInterval(interval);
      window.removeEventListener('focus', handleFocus);
    };
  }, []); // Callbacks stored in refs to avoid infinite loops

  const clearNewCount = useCallback(async () => {
    await syncService.clearNewCount();
    setStatus(prev => (prev ? { ...prev, new_transaction_count: 0 } : null));
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    await checkStatus();
  }, [checkStatus]);

  return { status, isLoading, clearNewCount, refresh };
}
