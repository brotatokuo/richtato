import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';
import { useEffect, useState } from 'react';
import { AccountFormFields } from './AccountFormFields';

interface AccountEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
  }) => Promise<void>;
  onDelete: () => void;
  initialValues: {
    name: string;
    type: string;
    entity: string;
  };
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  loading: boolean;
}

export function AccountEditModal({
  isOpen,
  onClose,
  onSubmit,
  onDelete,
  initialValues,
  accountTypeOptions,
  entityOptions,
  loading,
}: AccountEditModalProps) {
  const [form, setForm] = useState(initialValues);

  // Update form when initialValues change
  useEffect(() => {
    setForm(initialValues);
  }, [initialValues]);

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Account">
      <div className="space-y-4">
        <AccountFormFields
          form={form}
          onChange={handleFieldChange}
          accountTypeOptions={accountTypeOptions}
          entityOptions={entityOptions}
          idPrefix="edit-acc"
        />
        <div className="flex justify-between gap-2">
          <Button
            variant="destructive"
            onClick={() => {
              onClose();
              onDelete();
            }}
          >
            Delete
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!form.name || loading}>
              Save
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
