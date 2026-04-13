import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

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
  idPrefix?: string;
  showStartingBalance?: boolean;
}

export function AccountFormFields({
  form,
  onChange,
  accountTypeOptions,
  entityOptions,
  idPrefix = 'acc',
  showStartingBalance = false,
}: AccountFormFieldsProps) {
  return (
    <>
      <div>
        <Label htmlFor={`${idPrefix}-name`}>Name</Label>
        <Input
          id={`${idPrefix}-name`}
          value={form.name}
          onChange={e => onChange('name', e.target.value)}
          placeholder="e.g., Main Checking"
        />
      </div>
      <div>
        <Label htmlFor={`${idPrefix}-type`}>Type</Label>
        <Select value={form.type} onValueChange={v => onChange('type', v)}>
          <SelectTrigger id={`${idPrefix}-type`}>
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
      </div>
      <div>
        <Label htmlFor={`${idPrefix}-entity`}>Bank/Entity</Label>
        <Select value={form.entity} onValueChange={v => onChange('entity', v)}>
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
      {showStartingBalance && (
        <div>
          <Label htmlFor={`${idPrefix}-balance`}>
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
              id={`${idPrefix}-balance`}
              type="number"
              step="0.01"
              placeholder="0.00"
              value={form.starting_balance ?? ''}
              onChange={e => onChange('starting_balance', e.target.value)}
              className="pl-7"
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Current balance of this account when you start tracking it.
          </p>
        </div>
      )}
    </>
  );
}
