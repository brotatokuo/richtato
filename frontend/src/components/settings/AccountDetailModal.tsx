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
import { Account } from '@/lib/api/transactions';
import {
  AVAILABLE_CARD_IMAGES,
  getAutoDetectedImageKey,
} from '@/lib/imageMapping';
import { Check, Cloud, Lock, RefreshCw, Sparkles, Unlink } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AccountDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  account: Account | null;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
    image_key?: string | null;
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
    entity: '',
    imageKey: null as string | null,
  });

  // Find the matching entity option value for this account
  const findEntityValue = (account: Account): string => {
    // First try to match by entity slug
    if (account.entity) {
      const matchBySlug = entityOptions.find(
        e =>
          e.value === account.entity ||
          e.label.toLowerCase().replace(/\s+/g, '_') === account.entity
      );
      if (matchBySlug) return matchBySlug.value;
    }

    // Try to match by institution name
    if (account.institution_name) {
      const matchByName = entityOptions.find(
        e => e.label.toLowerCase() === account.institution_name?.toLowerCase()
      );
      if (matchByName) return matchByName.value;
    }

    // Try to match by entity_display
    if (account.entity_display) {
      const matchByDisplay = entityOptions.find(
        e => e.label === account.entity_display
      );
      if (matchByDisplay) return matchByDisplay.value;
    }

    return account.entity || '';
  };

  useEffect(() => {
    if (account && entityOptions.length > 0) {
      setForm({
        name: account.name || '',
        type: account.account_type || account.type || 'checking',
        entity: findEntityValue(account),
        imageKey: account.image_key ?? null,
      });
    }
  }, [account, entityOptions]);

  // Compute auto-detected image key based on current name (for credit cards)
  const autoDetectedImageKey = useMemo(
    () => getAutoDetectedImageKey(form.name),
    [form.name]
  );

  const isCreditCard = form.type === 'credit_card';

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit({
      name: form.name,
      type: form.type,
      entity: form.entity,
      image_key: form.imageKey,
    });
  };

  const handleImageSelect = (key: string | null) => {
    setForm(prev => ({ ...prev, imageKey: key }));
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

  const isConnected = account?.has_connection;

  // Get display values for locked fields
  const getTypeDisplayValue = () => {
    const option = accountTypeOptions.find(t => t.value === form.type);
    return option?.label || form.type;
  };

  const getEntityDisplayValue = () => {
    if (account?.institution_name) return account.institution_name;
    if (account?.entity_display) return account.entity_display;
    const option = entityOptions.find(e => e.value === form.entity);
    return option?.label || form.entity || 'Unknown';
  };

  if (!account) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Account Details">
      <div className="space-y-6">
        {/* Sync Status Section */}
        {isConnected && (
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
                disabled={
                  loading || account.connection_status === 'disconnected'
                }
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
        <div className="space-y-4">
          {/* Name - Always Editable */}
          <div>
            <Label htmlFor="detail-acc-name">Name</Label>
            <Input
              id="detail-acc-name"
              value={form.name}
              onChange={e => handleFieldChange('name', e.target.value)}
              placeholder="e.g., Main Checking"
            />
          </div>

          {/* Type - Locked for connected accounts */}
          <div>
            <Label htmlFor="detail-acc-type">Type</Label>
            {isConnected ? (
              <div
                className="flex items-center justify-between h-10 w-full rounded-md border border-input bg-muted/50 px-3 py-2 text-sm cursor-not-allowed"
                title="This field cannot be edited because the account is synced via Teller"
              >
                <span className="text-muted-foreground">
                  {getTypeDisplayValue()}
                </span>
                <Lock className="h-4 w-4 text-muted-foreground" />
              </div>
            ) : (
              <Select
                value={form.type}
                onValueChange={v => handleFieldChange('type', v)}
              >
                <SelectTrigger id="detail-acc-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {accountTypeOptions.map(t => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Entity - Locked for connected accounts */}
          <div>
            <Label htmlFor="detail-acc-entity">Bank/Entity</Label>
            {isConnected ? (
              <div
                className="flex items-center justify-between h-10 w-full rounded-md border border-input bg-muted/50 px-3 py-2 text-sm cursor-not-allowed"
                title="This field cannot be edited because the account is synced via Teller"
              >
                <span className="text-muted-foreground">
                  {getEntityDisplayValue()}
                </span>
                <Lock className="h-4 w-4 text-muted-foreground" />
              </div>
            ) : (
              <Select
                value={form.entity}
                onValueChange={v => handleFieldChange('entity', v)}
              >
                <SelectTrigger id="detail-acc-entity">
                  <SelectValue placeholder="Select a bank" />
                </SelectTrigger>
                <SelectContent>
                  {entityOptions.map(e => (
                    <SelectItem key={e.value} value={String(e.value)}>
                      {e.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        {/* Card Image Picker (for credit cards only) */}
        {isCreditCard && (
          <div>
            <Label className="mb-2 block">Card Background</Label>
            <div className="grid grid-cols-4 gap-2">
              {/* Auto-detect option */}
              <button
                type="button"
                onClick={() => handleImageSelect(null)}
                className={`relative aspect-[1.586] rounded-lg border-2 transition-all flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-800 ${
                  form.imageKey === null
                    ? 'border-primary ring-2 ring-primary/20'
                    : 'border-border hover:border-primary/50'
                }`}
                title="Auto-detect from card name"
              >
                <div className="flex flex-col items-center gap-0.5 text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  <span className="text-[10px] font-medium">Auto</span>
                </div>
                {form.imageKey === null && (
                  <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                    <Check className="h-3 w-3" />
                  </div>
                )}
              </button>

              {/* Card image options */}
              {AVAILABLE_CARD_IMAGES.map(img => {
                const isSelected = form.imageKey === img.key;
                const isAutoDetected =
                  form.imageKey === null && autoDetectedImageKey === img.key;

                return (
                  <button
                    key={img.key}
                    type="button"
                    onClick={() => handleImageSelect(img.key)}
                    className={`relative aspect-[1.586] rounded-lg border-2 transition-all overflow-hidden ${
                      isSelected
                        ? 'border-primary ring-2 ring-primary/20'
                        : isAutoDetected
                          ? 'border-primary/50 ring-1 ring-primary/10'
                          : 'border-border hover:border-primary/50'
                    }`}
                    title={img.label}
                  >
                    <img
                      src={img.path}
                      alt={img.label}
                      className="w-full h-full object-cover"
                    />
                    {isSelected && (
                      <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                        <Check className="h-3 w-3" />
                      </div>
                    )}
                    {isAutoDetected && !isSelected && (
                      <div className="absolute -top-1 -right-1 bg-muted text-muted-foreground rounded-full p-0.5">
                        <Sparkles className="h-3 w-3" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
            {form.imageKey === null && autoDetectedImageKey && (
              <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Auto-detected from card name
              </p>
            )}
            {form.imageKey === null && !autoDetectedImageKey && (
              <p className="text-xs text-muted-foreground mt-1.5">
                No match found — showing default card
              </p>
            )}
          </div>
        )}

        {/* Account Info */}
        {account.account_number_last4 && (
          <div className="text-sm text-muted-foreground">
            Account ending in:{' '}
            <span className="font-mono">
              ····{account.account_number_last4}
            </span>
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
