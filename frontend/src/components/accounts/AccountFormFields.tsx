import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useEffect, useMemo, useRef } from 'react';

export interface InstitutionFieldChoice {
  value: string;
  label: string;
  account_types: Array<{ value: string; label: string }>;
}

interface AccountFormFieldsProps {
  form: {
    name: string;
    type: string;
    entity: string;
    starting_balance?: string;
  };
  onChange: (
    field: 'name' | 'type' | 'entity' | 'starting_balance',
    value: string
  ) => void;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  institutions?: InstitutionFieldChoice[];
  idPrefix?: string;
  showStartingBalance?: boolean;
  autoFillName?: boolean;
}

function buildAutoAccountName(
  entity: string,
  type: string,
  entityOptions: Array<{ value: string; label: string }>,
  typeOptions: Array<{ value: string; label: string }>
): string {
  const entityLabel =
    entityOptions.find(option => option.value === entity)?.label ?? entity;
  const typeLabel =
    typeOptions.find(option => option.value === type)?.label ?? type;
  return `${entityLabel} ${typeLabel}`;
}

export function AccountFormFields({
  form,
  onChange,
  accountTypeOptions,
  entityOptions,
  institutions = [],
  idPrefix = 'acc',
  showStartingBalance = false,
  autoFillName = false,
}: AccountFormFieldsProps) {
  const nameManuallyEdited = useRef(false);

  const filteredTypeOptions = useMemo(() => {
    const institution = institutions.find(item => item.value === form.entity);
    if (institution?.account_types?.length) {
      return institution.account_types;
    }
    return accountTypeOptions;
  }, [accountTypeOptions, form.entity, institutions]);

  const suggestedName = useMemo(
    () =>
      buildAutoAccountName(
        form.entity,
        form.type,
        entityOptions,
        filteredTypeOptions
      ),
    [entityOptions, filteredTypeOptions, form.entity, form.type]
  );

  useEffect(() => {
    if (!autoFillName || nameManuallyEdited.current) {
      return;
    }

    if (form.name !== suggestedName) {
      onChange('name', suggestedName);
    }
  }, [autoFillName, form.name, onChange, suggestedName]);

  useEffect(() => {
    if (!autoFillName) {
      nameManuallyEdited.current = false;
    }
  }, [autoFillName]);

  const handleEntityChange = (value: string) => {
    onChange('entity', value);
    const institution = institutions.find(item => item.value === value);
    const nextTypeOptions = institution?.account_types?.length
      ? institution.account_types
      : accountTypeOptions;

    if (nextTypeOptions.length === 1) {
      onChange('type', nextTypeOptions[0].value);
      return;
    }

    if (!nextTypeOptions.some(option => option.value === form.type)) {
      onChange('type', nextTypeOptions[0]?.value ?? 'checking');
    }
  };

  return (
    <>
      <div>
        <Label htmlFor={`${idPrefix}-entity`}>Bank/Entity</Label>
        <Select value={form.entity} onValueChange={handleEntityChange}>
          <SelectTrigger id={`${idPrefix}-entity`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {entityOptions.map(e => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor={`${idPrefix}-type`}>Type</Label>
        <Select value={form.type} onValueChange={v => onChange('type', v)}>
          <SelectTrigger id={`${idPrefix}-type`}>
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
        <Label htmlFor={`${idPrefix}-name`}>Name</Label>
        <Input
          id={`${idPrefix}-name`}
          value={form.name}
          onChange={e => {
            nameManuallyEdited.current = true;
            onChange('name', e.target.value);
          }}
          placeholder="e.g., Chase Checking"
        />
      </div>
      {showStartingBalance && (
        <AccountOpeningBalanceField
          idPrefix={idPrefix}
          value={form.starting_balance ?? ''}
          onChange={value => onChange('starting_balance', value)}
        />
      )}
    </>
  );
}

interface AccountOpeningBalanceFieldProps {
  idPrefix: string;
  value: string;
  onChange: (value: string) => void;
}

export function AccountOpeningBalanceField({
  idPrefix,
  value,
  onChange,
}: AccountOpeningBalanceFieldProps) {
  return (
    <div>
      <Label htmlFor={`${idPrefix}-balance`}>
        Opening Balance{' '}
        <span className="text-muted-foreground font-normal">(optional)</span>
      </Label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
          $
        </span>
        <Input
          id={`${idPrefix}-balance`}
          type="number"
          step="0.01"
          placeholder="0.00"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="pl-7"
        />
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        Current balance of this account when you start tracking it.
      </p>
    </div>
  );
}
