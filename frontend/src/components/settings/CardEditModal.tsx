import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Modal } from '@/components/ui/Modal';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CardAccountItem } from '@/hooks/useCards';
import React from 'react';

interface CardEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string, bank: string) => Promise<void>;
  onDelete: () => void;
  card: CardAccountItem | null;
  bankOptions: Array<{ value: string; label: string }>;
}

export function CardEditModal({
  isOpen,
  onClose,
  onSubmit,
  onDelete,
  card,
  bankOptions,
}: CardEditModalProps) {
  const [name, setName] = React.useState('');
  const [bank, setBank] = React.useState('other');

  React.useEffect(() => {
    if (isOpen && card) {
      setName(card.name);
      setBank(card.bank);
    }
  }, [isOpen, card]);

  const handleSubmit = async () => {
    await onSubmit(name, bank);
    onClose();
  };

  const handleDelete = () => {
    onClose();
    onDelete();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Card">
      <div className="space-y-4">
        <div>
          <Label htmlFor="edit-card-name">Name</Label>
          <Input
            id="edit-card-name"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="edit-card-bank">Bank</Label>
          <Select value={bank} onValueChange={setBank}>
            <SelectTrigger id="edit-card-bank">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {bankOptions.map(b => (
                <SelectItem key={b.value} value={b.value}>
                  {b.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex justify-between gap-2">
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!name}>
              Save
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
