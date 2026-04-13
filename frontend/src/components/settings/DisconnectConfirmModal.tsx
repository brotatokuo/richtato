import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

interface DisconnectConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (deleteData: boolean) => Promise<void>;
  loading: boolean;
  accountName?: string;
}

export function DisconnectConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  loading,
  accountName,
}: DisconnectConfirmModalProps) {
  const [deleteOption, setDeleteOption] = useState<'connection' | 'all'>(
    'connection'
  );

  const handleConfirm = async () => {
    await onConfirm(deleteOption === 'all');
  };

  const handleClose = () => {
    setDeleteOption('connection');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Disconnect Bank Connection
          </DialogTitle>
          <DialogDescription>
            Choose how to disconnect{' '}
            {accountName ? `"${accountName}"` : 'this account'} from bank sync.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {/* Option 1: Remove connection only */}
          <label className="flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition">
            <input
              type="radio"
              name="deleteOption"
              value="connection"
              checked={deleteOption === 'connection'}
              onChange={() => setDeleteOption('connection')}
              className="mt-1"
            />
            <div>
              <div className="font-medium">Remove connection only</div>
              <div className="text-sm text-muted-foreground">
                Keep the account and all synced transactions. The account will
                become a manual account that you can update yourself.
              </div>
            </div>
          </label>

          {/* Option 2: Remove connection and delete data */}
          <label className="flex items-start gap-3 p-4 border border-red-200 rounded-lg cursor-pointer hover:bg-red-50/50 transition">
            <input
              type="radio"
              name="deleteOption"
              value="all"
              checked={deleteOption === 'all'}
              onChange={() => setDeleteOption('all')}
              className="mt-1"
            />
            <div>
              <div className="font-medium text-red-600">
                Remove connection and delete all data
              </div>
              <div className="text-sm text-muted-foreground">
                Permanently delete the account and all its transactions.{' '}
                <span className="text-red-600 font-medium">
                  This cannot be undone.
                </span>
              </div>
            </div>
          </label>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={deleteOption === 'all' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading
              ? 'Disconnecting...'
              : deleteOption === 'all'
                ? 'Disconnect & Delete'
                : 'Disconnect'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
