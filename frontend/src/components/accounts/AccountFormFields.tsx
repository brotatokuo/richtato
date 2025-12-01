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
  };
  onChange: (field: 'name' | 'type' | 'entity', value: string) => void;
  accountTypeOptions: Array<{ value: string; label: string }>;
  entityOptions: Array<{ value: string; label: string }>;
  idPrefix?: string;
}

export function AccountFormFields({
  form,
  onChange,
  accountTypeOptions,
  entityOptions,
  idPrefix = 'acc',
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
    </>
  );
}
