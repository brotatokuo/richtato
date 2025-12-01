import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { TellerSyncResult } from '@/lib/api/teller';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

interface TellerSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
  result: TellerSyncResult | null;
}

export function TellerSyncModal({
  isOpen,
  onClose,
  loading,
  result,
}: TellerSyncModalProps) {
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
            <div className="flex items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Please wait...</span>
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
                  <span className="text-muted-foreground">Accounts synced:</span>
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
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={onClose} disabled={loading}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
