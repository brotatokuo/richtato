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
import { useHousehold } from '@/contexts/HouseholdContext';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import {
  AVAILABLE_CARD_IMAGES,
  getAutoDetectedImageKey,
} from '@/lib/imageMapping';
import { Calendar, Check, Sparkles, Users } from 'lucide-react';
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
    image_key?: string | null;
    shared_with_household?: boolean;
    opening_balance?: number | null;
    opening_balance_date?: string | null;
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
    imageKey: null as string | null,
    sharedWithHousehold: false,
    openingBalance: '',
    openingBalanceDate: defaultOpeningBalanceDate(),
  });
  const [initialOpeningBalance, setInitialOpeningBalance] = useState('');

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
        console.info('[AccountEdit] loaded account detail for modal', {
          accountId: accountDetail.id,
          openingBalance,
          openingBalanceDate,
        });
        setForm({
          name: accountDetail.name || '',
          type: accountDetail.account_type || accountDetail.type || 'checking',
          entity: findEntityValue(accountDetail),
          imageKey: accountDetail.image_key ?? null,
          sharedWithHousehold: accountDetail.shared_with_household ?? false,
          openingBalance,
          openingBalanceDate,
        });
      })
      .catch(err => {
        if (cancelled) return;
        console.error(
          '[AccountEdit] failed to load account detail for modal',
          err
        );
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

  const autoDetectedImageKey = useMemo(
    () => getAutoDetectedImageKey(form.name),
    [form.name]
  );

  const isCreditCard = form.type === 'credit_card';

  const handleFieldChange = (
    field: 'name' | 'type' | 'entity' | 'openingBalance' | 'openingBalanceDate',
    value: string
  ) => {
    setForm(prev => ({ ...prev, [field]: value }));
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
      image_key?: string | null;
      shared_with_household?: boolean;
      opening_balance?: number | null;
      opening_balance_date?: string | null;
    } = {
      name: form.name,
      type: form.type,
      entity: form.entity,
      image_key: form.imageKey,
      shared_with_household: form.sharedWithHousehold,
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

    console.info('[AccountEdit] modal submit payload', {
      accountId: account?.id,
      openingBalanceChanged,
      initialOpeningBalance,
      initialOpeningBalanceDate,
      payload,
    });

    await onSubmit(payload);
  };

  const handleImageSelect = (key: string | null) => {
    setForm(prev => ({ ...prev, imageKey: key }));
  };

  return (
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

          {isCreditCard && (
            <div>
              <Label className="mb-2 block">Card Background</Label>
              <div className="grid grid-cols-4 gap-2">
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
                    form.sharedWithHousehold ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          )}

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
  );
}
