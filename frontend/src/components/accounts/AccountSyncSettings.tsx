import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { SyncMode } from '@/lib/api/transactions';
import { useEffect } from 'react';
import { Link } from 'react-router-dom';

const SYNC_MODE_OPTIONS: Array<{ value: SyncMode; label: string }> = [
  { value: 'upload', label: 'Statement Upload' },
  { value: 'manual', label: 'Manual Entry' },
];

export interface AccountSyncFormValues {
  entity: string;
  type: string;
  syncMode: SyncMode;
}

interface AccountSyncSettingsProps {
  form: AccountSyncFormValues;
  hasStorageUri?: boolean;
  onChange: (field: 'syncMode', value: SyncMode) => void;
  idPrefix?: string;
  disabled?: boolean;
}

export function AccountSyncSettings({
  form,
  hasStorageUri = true,
  onChange,
  idPrefix = 'sync',
  disabled = false,
}: AccountSyncSettingsProps) {
  const uploadNeedsDrive = !hasStorageUri;

  useEffect(() => {
    if (form.syncMode === 'upload' && uploadNeedsDrive) {
      onChange('syncMode', 'manual');
    }
  }, [form.syncMode, onChange, uploadNeedsDrive]);

  return (
    <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-3">
      <div>
        <Label htmlFor={`${idPrefix}-mode`}>Import Method</Label>
        <Select
          value={form.syncMode}
          disabled={disabled}
          onValueChange={value => onChange('syncMode', value as SyncMode)}
        >
          <SelectTrigger id={`${idPrefix}-mode`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SYNC_MODE_OPTIONS.map(option => (
              <SelectItem
                key={option.value}
                value={option.value}
                disabled={option.value === 'upload' && uploadNeedsDrive}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!hasStorageUri && (
        <p className="rounded-md border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
          Statement uploads need Google Drive. You can still create this account
          with manual tracking, then activate Drive in{' '}
          <Link
            to="/setup?tab=statements"
            className="font-medium text-foreground underline underline-offset-2"
          >
            Setup → Statements
          </Link>
          .
        </p>
      )}
    </div>
  );
}
