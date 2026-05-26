import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';
import { useState } from 'react';
import {
  AccountFormFields,
  type InstitutionFieldChoice,
} from './AccountFormFields';
import {
  AccountSyncSettings,
  type AccountSyncFormValues,
} from './AccountSyncSettings';
import type { AgentCadence, SyncMode } from '@/lib/api/bankSync';
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
    agent_cadence: AgentCadence;
    agent_sync_hour: number;
    agent_activity_url?: string;
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
  sync_mode: 'manual' as SyncMode,
  agent_cadence: 'daily' as AgentCadence,
  agent_sync_hour: 6,
  agent_activity_url: '',
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

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity' | 'starting_balance',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSyncChange = (
    field: keyof Pick<
      AccountSyncFormValues,
      'syncMode' | 'agentCadence' | 'agentSyncHour' | 'agentActivityUrl'
    >,
    value: string | number
  ) => {
    const fieldMap = {
      syncMode: 'sync_mode',
      agentCadence: 'agent_cadence',
      agentSyncHour: 'agent_sync_hour',
      agentActivityUrl: 'agent_activity_url',
    } as const;
    setForm(prev => ({ ...prev, [fieldMap[field]]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
    setForm(EMPTY_FORM);
  };

  const handleClose = () => {
    setForm(EMPTY_FORM);
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
          institutions={institutions}
          idPrefix="acc"
          showStartingBalance
        />
        <AccountSyncSettings
          form={{
            entity: form.entity,
            type: form.type,
            syncMode: form.sync_mode,
            agentCadence: form.agent_cadence,
            agentSyncHour: form.agent_sync_hour,
            agentActivityUrl: form.agent_activity_url,
          }}
          onChange={handleSyncChange}
          institutions={institutions}
          hasStorageUri={isDriveActive}
          idPrefix="acc-sync"
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
