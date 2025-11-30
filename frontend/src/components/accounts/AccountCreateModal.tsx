import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';
import { useState } from 'react';
import { AccountFormFields } from './AccountFormFields';

interface AccountCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
  }) => Promise<void>;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  loading: boolean;
}

export function AccountCreateModal({
  isOpen,
  onClose,
  onSubmit,
  accountTypeOptions,
  entityOptions,
  loading,
}: AccountCreateModalProps) {
  const [form, setForm] = useState({
    name: '',
    type: 'checking',
    entity: 'other',
  });

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
    // Reset form after successful submission
    setForm({ name: '', type: 'checking', entity: 'other' });
  };

  const handleClose = () => {
    setForm({ name: '', type: 'checking', entity: 'other' });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Account">
      <div className="space-y-4">
        <AccountFormFields
          form={form}
          onChange={handleFieldChange}
          accountTypeOptions={accountTypeOptions}
          entityOptions={entityOptions}
          idPrefix="acc"
        />
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!form.name || loading}>
            Create
          </Button>
        </div>
      </div>
    </Modal>
  );
}
