import { useEffect, useRef } from 'react';

/**
 * Generic polling hook that calls `fetchFn` on an interval until
 * `isTerminal` returns true for the result, or the hook unmounts.
 *
 * @param fetchFn    Async function to call each tick.
 * @param intervalMs Milliseconds between ticks (default 1000).
 * @param isTerminal Predicate — when it returns true, polling stops.
 * @param enabled    Set false to pause polling without unmounting.
 */
export function usePolling<T>(
  fetchFn: () => Promise<T>,
  {
    intervalMs = 1000,
    isTerminal,
    enabled = true,
    onResult,
    onError,
  }: {
    intervalMs?: number;
    isTerminal: (data: T) => boolean;
    enabled?: boolean;
    onResult?: (data: T) => void;
    onError?: (error: unknown) => void;
  }
) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;
    stoppedRef.current = false;

    const poll = async () => {
      try {
        const data = await fetchFn();
        if (stoppedRef.current) return;
        onResult?.(data);
        if (isTerminal(data)) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (error) {
        if (!stoppedRef.current) {
          onError?.(error);
        }
      }
    };

    poll();
    intervalRef.current = setInterval(poll, intervalMs);

    return () => {
      stoppedRef.current = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled]); // eslint-disable-line react-hooks/exhaustive-deps
}
