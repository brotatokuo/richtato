import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface TellerDisconnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  loading?: boolean;
  institutionName?: string;
}

export function TellerDisconnectModal({
  isOpen,
  onClose,
  onConfirm,
  loading = false,
  institutionName,
}: TellerDisconnectModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disconnect Bank Account</DialogTitle>
          <DialogDescription>
            Are you sure you want to disconnect{' '}
            {institutionName ? `${institutionName}` : 'this account'}? This will
            stop syncing transactions, but your existing data will be preserved.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={loading} variant="destructive">
            {loading ? 'Disconnecting...' : 'Disconnect'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
