import React from 'react';
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

interface CardCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string, bank: string) => Promise<void>;
  bankOptions: Array<{ value: string; label: string }>;
}

export function CardCreateModal({
  isOpen,
  onClose,
  onSubmit,
  bankOptions,
}: CardCreateModalProps) {
  const [name, setName] = React.useState('');
  const [bank, setBank] = React.useState('other');

  React.useEffect(() => {
    if (isOpen) {
      setName('');
      setBank('other');
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    await onSubmit(name, bank);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Card">
      <div className="space-y-4">
        <div>
          <Label htmlFor="card-name">Name</Label>
          <Input
            id="card-name"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g., Sapphire Preferred"
          />
        </div>
        <div>
          <Label htmlFor="card-bank">Bank</Label>
          <Select value={bank} onValueChange={setBank}>
            <SelectTrigger id="card-bank">
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
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name}>
            Add
          </Button>
        </div>
      </div>
    </Modal>
  );
}
