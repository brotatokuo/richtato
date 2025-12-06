import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/Modal';
import { Account } from '@/lib/api/transactions';
import { AccountFormFields } from '@/components/accounts/AccountFormFields';
import { Cloud, RefreshCw, Unlink } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AccountDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  account: Account | null;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
  }) => Promise<void>;
  onDelete: () => void;
  onSync: () => void;
  onDisconnect: () => void;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  loading: boolean;
}

export function AccountDetailModal({
  isOpen,
  onClose,
  account,
  onSubmit,
  onDelete,
  onSync,
  onDisconnect,
  accountTypeOptions,
  entityOptions,
  loading,
}: AccountDetailModalProps) {
  const [form, setForm] = useState({
    name: '',
    type: 'checking',
    entity: 'other',
  });

  useEffect(() => {
    if (account) {
      setForm({
        name: account.name || '',
        type: account.account_type || account.type || 'checking',
        entity: account.entity || 'other',
      });
    }
  }, [account]);

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit(form);
  };

  const formatLastSync = (lastSync: string | null | undefined) => {
    if (!lastSync) return 'Never';
    try {
      const date = new Date(lastSync);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };

  const statusColors: Record<string, string> = {
    active: 'text-green-600',
    error: 'text-red-600',
    disconnected: 'text-gray-500',
  };

  if (!account) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Account Details">
      <div className="space-y-6">
        {/* Sync Status Section */}
        {account.has_connection && (
          <div className="p-4 bg-muted/50 rounded-lg space-y-3">
            <div className="flex items-center gap-2">
              <Cloud
                className={`h-5 w-5 ${statusColors[account.connection_status || 'active']}`}
              />
              <span className="font-medium">Connected via Teller</span>
              <span
                className={`text-sm ${statusColors[account.connection_status || 'active']}`}
              >
                ({account.connection_status || 'active'})
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              Last synced: {formatLastSync(account.last_sync)}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onSync}
                disabled={loading || account.connection_status === 'disconnected'}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Sync Now
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onDisconnect}
                disabled={loading}
                className="text-orange-600 hover:text-orange-700"
              >
                <Unlink className="h-4 w-4 mr-2" />
                Disconnect
              </Button>
            </div>
          </div>
        )}

        {/* Account Form Fields */}
        <AccountFormFields
          form={form}
          onChange={handleFieldChange}
          accountTypeOptions={accountTypeOptions}
          entityOptions={entityOptions}
          idPrefix="detail-acc"
        />

        {/* Account Info */}
        {account.account_number_last4 && (
          <div className="text-sm text-muted-foreground">
            Account ending in: <span className="font-mono">····{account.account_number_last4}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between gap-2 pt-4 border-t">
          <Button
            variant="destructive"
            onClick={() => {
              onClose();
              onDelete();
            }}
            disabled={loading}
          >
            Delete Account
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!form.name || loading}>
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
