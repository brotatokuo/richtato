import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { SyncJobProgress, TellerSyncResult } from '@/lib/api/teller';
import { AlertCircle, CheckCircle2, Clock, Loader2, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

interface TellerSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
  result: TellerSyncResult | null;
  progress?: SyncJobProgress | null;
}

export function TellerSyncModal({
  isOpen,
  onClose,
  loading,
  result,
  progress,
}: TellerSyncModalProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer effect when loading
  useEffect(() => {
    if (!loading) {
      setElapsedSeconds(0);
      return;
    }
    const interval = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [loading]);

  // Playful messages based on elapsed time
  const getStatusMessage = () => {
    if (elapsedSeconds < 5) return 'Starting sync...';
    if (elapsedSeconds < 15) return 'Fetching transactions...';
    if (elapsedSeconds < 30) return 'Still working... free API has rate limits 😅';
    if (elapsedSeconds < 60) return 'Taking a breather to stay under API limits 🐢';
    if (elapsedSeconds < 90) return 'Patience is a virtue... almost there! ☕';
    if (elapsedSeconds < 120) return 'Still chugging along... grab a snack? 🍿';
    return 'This is taking a while, but we got this! 💪';
  };

  // Format elapsed time as "1m 23s"
  const formatElapsed = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Sync Transactions</DialogTitle>
          <DialogDescription>
            {loading
              ? 'Syncing your transactions from Teller...'
              : result?.success
                ? 'Sync completed successfully!'
                : 'Sync completed with errors'}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {loading && (
            <div className="space-y-4">
              <div className="flex flex-col items-center gap-3 text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="text-center">{getStatusMessage()}</span>

                {/* Prominent transaction counter */}
                <div className="flex flex-col items-center gap-1 py-2">
                  <span className="text-3xl font-bold tabular-nums text-foreground">
                    {(progress?.transactions_synced ?? 0).toLocaleString()}
                  </span>
                  <span className="text-xs text-muted-foreground">transactions synced</span>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-muted-foreground/70">
                  <Clock className="h-3 w-3" />
                  <span className="tabular-nums">{formatElapsed(elapsedSeconds)}</span>
                </div>
              </div>
              {progress?.status === 'running' && (progress.transactions_skipped > 0 || progress.batches_processed > 0) && (
                <div className="bg-muted/50 rounded-lg p-3 space-y-1.5">
                  {progress.transactions_skipped > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">
                        Skipped (duplicates):
                      </span>
                      <span className="tabular-nums text-muted-foreground">
                        {progress.transactions_skipped.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {progress.batches_processed > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">
                        Batches processed:
                      </span>
                      <span className="tabular-nums text-muted-foreground">
                        {progress.batches_processed}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {!loading && result && (
            <div className="space-y-3">
              {result.success ? (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">{result.message}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-5 w-5" />
                  <span className="font-medium">{result.message}</span>
                </div>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Accounts synced:
                  </span>
                  <span className="font-medium">{result.accounts_synced}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Transactions synced:
                  </span>
                  <span className="font-medium">
                    {result.transactions_synced}
                  </span>
                </div>
              </div>

              {result.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 rounded-md">
                  <div className="text-sm font-medium text-red-800 mb-2">
                    Errors:
                  </div>
                  <ul className="text-sm text-red-700 space-y-1">
                    {result.errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.success &&
                (result.accounts_synced > 0 ||
                  result.transactions_synced > 0) && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-md border border-blue-200">
                    <div className="text-sm text-blue-800">
                      <strong>💡 Note:</strong> New accounts and transactions
                      have been added. Refresh the page to see them in the
                      Accounts and Data sections.
                    </div>
                  </div>
                )}
            </div>
          )}
        </div>

        <DialogFooter>
          {!loading && result?.success && (
            <Button onClick={handleRefresh} variant="default" className="mr-2">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Page
            </Button>
          )}
          <Button onClick={onClose} disabled={loading} variant="outline">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
