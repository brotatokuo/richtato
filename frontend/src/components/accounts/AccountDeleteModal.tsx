import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';

interface AccountDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  loading: boolean;
}

export function AccountDeleteModal({
  isOpen,
  onClose,
  onConfirm,
  loading,
}: AccountDeleteModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Account">
      <div className="space-y-4">
        <p>Are you sure you want to delete this account?</p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            Delete
          </Button>
        </div>
      </div>
    </Modal>
  );
}
