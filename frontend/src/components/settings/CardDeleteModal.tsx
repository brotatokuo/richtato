import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';

interface CardDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export function CardDeleteModal({
  isOpen,
  onClose,
  onConfirm,
}: CardDeleteModalProps) {
  const handleConfirm = async () => {
    await onConfirm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Card">
      <div className="space-y-4">
        <p>Are you sure you want to delete this card?</p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleConfirm}>
            Delete
          </Button>
        </div>
      </div>
    </Modal>
  );
}
