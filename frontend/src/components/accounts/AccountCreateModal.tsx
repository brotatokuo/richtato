import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';
import { useState } from 'react';
import {
  AccountFormFields,
  AccountOpeningBalanceField,
  type InstitutionFieldChoice,
} from './AccountFormFields';
import { AccountSyncSettings } from './AccountSyncSettings';
import type { SyncMode } from '@/lib/api/transactions';
import { useDrive } from '@/contexts/DriveContext';

interface AccountCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
    starting_balance?: string;
    sync_mode: SyncMode;
  }) => Promise<void>;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  institutions?: InstitutionFieldChoice[];
  loading: boolean;
}

const EMPTY_FORM = {
  name: '',
  type: 'checking',
  entity: 'other',
  starting_balance: '',
  sync_mode: 'upload' as SyncMode,
};

export function AccountCreateModal({
  isOpen,
  onClose,
  onSubmit,
  accountTypeOptions,
  entityOptions,
  institutions = [],
  loading,
}: AccountCreateModalProps) {
  const { isDriveActive } = useDrive();
  const [form, setForm] = useState(EMPTY_FORM);
  const [formSession, setFormSession] = useState(0);

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity' | 'starting_balance',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSyncChange = (_field: 'syncMode', value: SyncMode) => {
    setForm(prev => ({ ...prev, sync_mode: value }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
    setForm(EMPTY_FORM);
    setFormSession(session => session + 1);
  };

  const handleClose = () => {
    setForm(EMPTY_FORM);
    setFormSession(session => session + 1);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Account">
      <div className="space-y-4">
        <AccountFormFields
          key={formSession}
          form={form}
          onChange={handleFieldChange}
          accountTypeOptions={accountTypeOptions}
          entityOptions={entityOptions}
          institutions={institutions}
          idPrefix="acc"
          autoFillName
        />
        <AccountSyncSettings
          form={{
            entity: form.entity,
            type: form.type,
            syncMode: form.sync_mode,
          }}
          onChange={handleSyncChange}
          hasStorageUri={isDriveActive}
          idPrefix="acc-sync"
        />
        {form.sync_mode === 'manual' && (
          <AccountOpeningBalanceField
            idPrefix="acc"
            value={form.starting_balance}
            onChange={value => handleFieldChange('starting_balance', value)}
          />
        )}
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
