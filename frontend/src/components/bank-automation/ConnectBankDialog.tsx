import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  bankAutomationApi,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { CheckCircle2, ChromeIcon, Loader2, RefreshCcw } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface ConnectBankDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnected: (connection: BankAutomationConnection) => void;
  initialConnectionIds: number[];
}

const POLL_INTERVAL_MS = 3000;

export function ConnectBankDialog({
  open,
  onOpenChange,
  onConnected,
  initialConnectionIds,
}: ConnectBankDialogProps) {
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detected, setDetected] = useState<BankAutomationConnection | null>(
    null
  );
  const seenIds = useRef<Set<number>>(new Set(initialConnectionIds));
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    seenIds.current = new Set(initialConnectionIds);
  }, [initialConnectionIds]);

  useEffect(() => {
    if (!open) {
      setPolling(false);
      setDetected(null);
      setError(null);
      if (timer.current) {
        clearInterval(timer.current);
        timer.current = null;
      }
    }
  }, [open]);

  const startPolling = () => {
    setPolling(true);
    setError(null);
    setDetected(null);
    if (timer.current) clearInterval(timer.current);

    timer.current = setInterval(async () => {
      try {
        const list = await bankAutomationApi.listConnections();
        const fresh = list.find(c => !seenIds.current.has(c.id));
        if (fresh) {
          setDetected(fresh);
          setPolling(false);
          if (timer.current) {
            clearInterval(timer.current);
            timer.current = null;
          }
          onConnected(fresh);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to poll for new connection'
        );
      }
    }, POLL_INTERVAL_MS);
  };

  const handleClose = () => onOpenChange(false);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ChromeIcon className="h-5 w-5" /> Connect a bank
          </DialogTitle>
          <DialogDescription>
            Bank passwords stay in your bank's site. The Richtato Chrome
            extension only sends an authenticated session token.
          </DialogDescription>
        </DialogHeader>

        <ol className="space-y-3 text-sm text-foreground">
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              1
            </span>
            <span>
              Install the{' '}
              <span className="font-medium">Richtato Bank Sync</span> Chrome
              extension and configure it with your Richtato URL.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              2
            </span>
            <span>
              In Chrome, open your bank in a new tab and sign in normally (with
              MFA if enabled).
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              3
            </span>
            <span>
              Open the activity page for the account you want to sync, then
              click the Richtato extension icon and press{' '}
              <span className="font-medium">Sync this account</span>.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              4
            </span>
            <span>
              Click "Watch for connection" below. We'll poll every few seconds
              and confirm here when the capture lands.
            </span>
          </li>
        </ol>

        {detected ? (
          <div className="flex items-center gap-2 rounded-md border border-emerald-500/40 bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" />
            Connected to {detected.institution_name}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={handleClose}>
            Close
          </Button>
          {detected ? (
            <Button onClick={handleClose}>Done</Button>
          ) : polling ? (
            <Button disabled className="gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Watching...
            </Button>
          ) : (
            <Button onClick={startPolling} className="gap-2">
              <RefreshCcw className="h-4 w-4" />
              Watch for connection
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
