import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Modal } from '@/components/ui/Modal';
import { AccountSyncSettings } from '@/components/accounts/AccountSyncSettings';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useHousehold } from '@/contexts/HouseholdContext';
import {
  Account,
  transactionsApiService,
  type SyncMode,
} from '@/lib/api/transactions';
import { Calendar, Users } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import type { InstitutionFieldChoice } from '@/components/accounts/AccountFormFields';

interface AccountDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  account: Account | null;
  onSubmit: (form: {
    name: string;
    type: string;
    entity: string;
    shared_with_household?: boolean;
    opening_balance?: number | null;
    opening_balance_date?: string | null;
    sync_mode?: SyncMode;
  }) => Promise<void>;
  onDelete: () => void;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  institutions?: InstitutionFieldChoice[];
  loading: boolean;
}

function defaultOpeningBalanceDate(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function AccountDetailModal({
  isOpen,
  onClose,
  account,
  onSubmit,
  onDelete,
  accountTypeOptions,
  entityOptions,
  institutions = [],
  loading,
}: AccountDetailModalProps) {
  const { isInHousehold } = useHousehold();
  const dateInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    name: '',
    type: 'checking',
    entity: '',
    sharedWithHousehold: false,
    openingBalance: '',
    openingBalanceDate: defaultOpeningBalanceDate(),
    syncMode: 'manual' as SyncMode,
    hasStorageUri: false,
  });
  const [initialOpeningBalance, setInitialOpeningBalance] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  const filteredTypeOptions = useMemo(() => {
    const institution = institutions.find(item => item.value === form.entity);
    if (institution?.account_types?.length) {
      return institution.account_types;
    }
    return accountTypeOptions;
  }, [accountTypeOptions, form.entity, institutions]);

  const handleEntityChange = (value: string) => {
    setForm(prev => {
      const institution = institutions.find(item => item.value === value);
      const nextTypeOptions = institution?.account_types?.length
        ? institution.account_types
        : accountTypeOptions;
      let nextType = prev.type;
      if (nextTypeOptions.length === 1) {
        nextType = nextTypeOptions[0].value;
      } else if (!nextTypeOptions.some(option => option.value === prev.type)) {
        nextType = nextTypeOptions[0]?.value ?? 'checking';
      }
      return { ...prev, entity: value, type: nextType };
    });
  };
  const [initialOpeningBalanceDate, setInitialOpeningBalanceDate] = useState(
    defaultOpeningBalanceDate()
  );
  const [loadingOpeningBalance, setLoadingOpeningBalance] = useState(false);
  const deleteConfirmationPhrase = account?.name.trim() ?? '';
  const isDeleteConfirmed =
    deleteConfirmation.trim() === deleteConfirmationPhrase;

  const findEntityValue = (accountRecord: Account): string => {
    if (accountRecord.entity) {
      const matchBySlug = entityOptions.find(
        e =>
          e.value === accountRecord.entity ||
          e.label.toLowerCase().replace(/\s+/g, '_') === accountRecord.entity
      );
      if (matchBySlug) return matchBySlug.value;
    }

    if (accountRecord.institution_name) {
      const matchByName = entityOptions.find(
        e =>
          e.label.toLowerCase() ===
          accountRecord.institution_name?.toLowerCase()
      );
      if (matchByName) return matchByName.value;
    }

    if (accountRecord.entity_display) {
      const matchByDisplay = entityOptions.find(
        e => e.label === accountRecord.entity_display
      );
      if (matchByDisplay) return matchByDisplay.value;
    }

    return accountRecord.entity || '';
  };

  useEffect(() => {
    if (!account || entityOptions.length === 0 || !isOpen) return;

    let cancelled = false;
    setLoadingOpeningBalance(true);

    transactionsApiService
      .getAccountById(account.id)
      .then(accountDetail => {
        if (cancelled) return;

        const openingBalance = accountDetail.opening_balance ?? '';
        const openingBalanceDate =
          accountDetail.opening_balance_date ?? defaultOpeningBalanceDate();

        setInitialOpeningBalance(openingBalance);
        setInitialOpeningBalanceDate(openingBalanceDate);
        setForm({
          name: accountDetail.name || '',
          type: accountDetail.account_type || accountDetail.type || 'checking',
          entity: findEntityValue(accountDetail),
          sharedWithHousehold: accountDetail.shared_with_household ?? false,
          openingBalance,
          openingBalanceDate,
          syncMode: accountDetail.sync_mode ?? 'manual',
          hasStorageUri: Boolean(accountDetail.resolved_storage_uri),
        });
      })
      .catch(err => {
        if (cancelled) return;
        toast.error('Failed to load account details', {
          description: err instanceof Error ? err.message : undefined,
        });
      })
      .finally(() => {
        if (!cancelled) setLoadingOpeningBalance(false);
      });

    return () => {
      cancelled = true;
    };
    // findEntityValue depends on entityOptions which is already in deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account, entityOptions, isOpen]);

  useEffect(() => {
    if (!isOpen) {
      setShowDeleteConfirm(false);
      setDeleteConfirmation('');
    }
  }, [isOpen]);

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity' | 'openingBalance' | 'openingBalanceDate',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSyncChange = (_field: 'syncMode', value: SyncMode) => {
    setForm(prev => ({ ...prev, syncMode: value }));
  };

  const handleSubmit = async () => {
    const trimmedOpeningBalance = form.openingBalance.trim();
    const openingBalanceChanged =
      trimmedOpeningBalance !== initialOpeningBalance.trim() ||
      (trimmedOpeningBalance !== '' &&
        form.openingBalanceDate !== initialOpeningBalanceDate);

    const payload: {
      name: string;
      type: string;
      entity: string;
      shared_with_household?: boolean;
      opening_balance?: number | null;
      opening_balance_date?: string | null;
      sync_mode?: SyncMode;
    } = {
      name: form.name,
      type: form.type,
      entity: form.entity,
      shared_with_household: form.sharedWithHousehold,
      sync_mode: form.syncMode,
    };

    if (openingBalanceChanged) {
      if (!trimmedOpeningBalance) {
        payload.opening_balance = null;
        payload.opening_balance_date = null;
      } else {
        const parsed = Number.parseFloat(trimmedOpeningBalance);
        if (Number.isNaN(parsed)) {
          toast.error('Enter a valid opening balance');
          return;
        }
        payload.opening_balance = parsed;
        payload.opening_balance_date = form.openingBalanceDate || null;
      }
    }

    await onSubmit(payload);
  };

  return (
    <>
      <Modal
        isOpen={isOpen && !!account}
        onClose={onClose}
        title="Account Details"
      >
        {account && (
          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="detail-acc-name">Name</Label>
                <Input
                  id="detail-acc-name"
                  value={form.name}
                  onChange={e => handleFieldChange('name', e.target.value)}
                  placeholder="e.g., Main Checking"
                />
              </div>

              <div>
                <Label htmlFor="detail-acc-type">Type</Label>
                <Select
                  value={form.type}
                  onValueChange={v => handleFieldChange('type', v)}
                >
                  <SelectTrigger id="detail-acc-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredTypeOptions.map(t => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="detail-acc-entity">Bank/Entity</Label>
                <Select value={form.entity} onValueChange={handleEntityChange}>
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
              </div>

              <div>
                <Label htmlFor="detail-acc-opening-balance">
                  Opening Balance{' '}
                  <span className="text-muted-foreground font-normal">
                    (optional)
                  </span>
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                    $
                  </span>
                  <Input
                    id="detail-acc-opening-balance"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={form.openingBalance}
                    onChange={e =>
                      handleFieldChange('openingBalance', e.target.value)
                    }
                    className="pl-7"
                    disabled={loadingOpeningBalance}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Balance this account had when you started tracking it. Leave
                  blank to remove an existing opening balance.
                </p>
              </div>

              <div>
                <Label htmlFor="detail-acc-opening-date">
                  Opening Balance Date
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    ref={dateInputRef}
                    id="detail-acc-opening-date"
                    type="date"
                    value={form.openingBalanceDate}
                    onChange={e =>
                      handleFieldChange('openingBalanceDate', e.target.value)
                    }
                    className="flex-1"
                    disabled={
                      loadingOpeningBalance || !form.openingBalance.trim()
                    }
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => dateInputRef.current?.showPicker?.()}
                    title="Open calendar"
                    disabled={
                      loadingOpeningBalance || !form.openingBalance.trim()
                    }
                  >
                    <Calendar className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <AccountSyncSettings
              form={{
                entity: form.entity,
                type: form.type,
                syncMode: form.syncMode,
              }}
              onChange={handleSyncChange}
              hasStorageUri={form.hasStorageUri}
              idPrefix="detail-sync"
              disabled={loadingOpeningBalance}
            />

            {account.account_number_last4 && (
              <div className="text-sm text-muted-foreground">
                Account ending in:{' '}
                <span className="font-mono">
                  ····{account.account_number_last4}
                </span>
              </div>
            )}

            {isInHousehold && (
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Share with Household</p>
                    <p className="text-xs text-muted-foreground">
                      Include this account in your household dashboard
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={form.sharedWithHousehold}
                  onClick={() =>
                    setForm(prev => ({
                      ...prev,
                      sharedWithHousehold: !prev.sharedWithHousehold,
                    }))
                  }
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    form.sharedWithHousehold ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-background shadow-lg ring-0 transition-transform ${
                      form.sharedWithHousehold
                        ? 'translate-x-5'
                        : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            )}

            <div className="flex justify-between gap-2 pt-4 border-t">
              <Button
                variant="destructive"
                onClick={() => setShowDeleteConfirm(true)}
                disabled={loading}
              >
                Delete Account
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!form.name || loading || loadingOpeningBalance}
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        )}
      </Modal>

      <AlertDialog
        open={showDeleteConfirm}
        onOpenChange={open => {
          setShowDeleteConfirm(open);
          if (!open) setDeleteConfirmation('');
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this account?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the account and its related history from
              Richtato. To confirm, type the account name exactly as shown.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="space-y-2">
            <p className="rounded-md bg-muted px-3 py-2 text-sm font-medium text-foreground">
              {deleteConfirmationPhrase}
            </p>
            <div className="space-y-1">
              <Label htmlFor="delete-account-confirmation">Account name</Label>
              <Input
                id="delete-account-confirmation"
                value={deleteConfirmation}
                onChange={e => setDeleteConfirmation(e.target.value)}
                placeholder={deleteConfirmationPhrase}
                autoComplete="off"
                autoFocus
              />
            </div>
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel disabled={loading}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={!isDeleteConfirmed || loading}
              onClick={event => {
                event.preventDefault();
                if (!isDeleteConfirmed || loading) return;
                setShowDeleteConfirm(false);
                setDeleteConfirmation('');
                onDelete();
              }}
            >
              Delete Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
