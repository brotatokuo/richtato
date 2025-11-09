import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Account, Category } from '@/lib/api/transactions';
import { TransactionFormData, TransactionType } from '@/types/transactions';
import { Minus, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
});

interface TransactionFormProps {
  type: TransactionType;
  formData: TransactionFormData;
  onFormChange: (data: TransactionFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  accounts: Account[];
  categories: Category[];
  submitLabel?: string;
  onDelete?: () => void;
}

export function TransactionForm({
  type,
  formData,
  onFormChange,
  onSubmit,
  accounts,
  categories,
  submitLabel,
  onDelete,
}: TransactionFormProps) {
  const isIncome = type === 'income';
  const title = isIncome ? 'Income' : 'Expense';
  const placeholder = isIncome
    ? 'e.g., Salary, Freelance work'
    : 'e.g., Groceries, Gas, Coffee';

  const evaluateExpression = (expr: string): number | null => {
    const trimmed = expr.trim().replace(/\s+/g, '');
    if (!/^[0-9+\-*/().]+$/.test(trimmed)) return null;
    try {
      const result = Function('"use strict"; return (' + trimmed + ')')();
      return typeof result === 'number' && isFinite(result) ? result : null;
    } catch {
      return null;
    }
  };

  const formatAmount = (value: number): string => {
    return (Math.round(value * 100) / 100).toFixed(2);
  };

  const normalizeNumericString = (val: string): string => {
    return val.replace(/[,$\s]/g, '');
  };

  const [amountDisplay, setAmountDisplay] = useState<string>(
    formData.amount || ''
  );
  const [isAmountFocused, setIsAmountFocused] = useState<boolean>(false);

  useEffect(() => {
    // When external form data changes (e.g., opening modal), reflect as currency unless focused or expression
    if (!isAmountFocused) {
      if (!formData.amount) {
        setAmountDisplay('');
      } else if (String(formData.amount).trim().startsWith('=')) {
        setAmountDisplay(formData.amount);
      } else {
        const num = parseFloat(normalizeNumericString(String(formData.amount)));
        if (!isNaN(num)) {
          setAmountDisplay(currencyFormatter.format(Math.abs(num)));
        } else {
          setAmountDisplay(formData.amount);
        }
      }
    }
  }, [formData.amount, isAmountFocused]);

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor={`${type}-description`}>Description</Label>
          <Input
            id={`${type}-description`}
            value={formData.description}
            onChange={e =>
              onFormChange({
                ...formData,
                description: e.target.value,
              })
            }
            placeholder={placeholder}
            required
          />
        </div>
        <div>
          <Label htmlFor={`${type}-amount`}>Amount</Label>
          {isIncome ? (
            <Input
              id={`${type}-amount`}
              type="text"
              value={amountDisplay}
              onFocus={() => {
                setIsAmountFocused(true);
                if (!amountDisplay) return;
                // Show raw numeric for editing if currently formatted currency
                if (!amountDisplay.trim().startsWith('=')) {
                  const raw = normalizeNumericString(amountDisplay);
                  setAmountDisplay(raw);
                }
              }}
              onChange={e => {
                const rawInput = e.target.value;
                setAmountDisplay(rawInput);
                if (rawInput.trim().startsWith('=')) {
                  onFormChange({
                    ...formData,
                    amount: rawInput,
                  });
                } else {
                  const normalized = normalizeNumericString(rawInput);
                  onFormChange({
                    ...formData,
                    amount: normalized,
                  });
                }
              }}
              onBlur={e => {
                setIsAmountFocused(false);
                const val = e.target.value;
                if (val.trim().startsWith('=')) {
                  const result = evaluateExpression(val.trim().slice(1));
                  if (result !== null) {
                    const normalized = Math.abs(result); // don't affect sign toggle elsewhere
                    const numericString = formatAmount(normalized);
                    onFormChange({ ...formData, amount: numericString });
                    setAmountDisplay(currencyFormatter.format(normalized));
                  }
                  return;
                }
                const normalized = normalizeNumericString(val);
                const num = parseFloat(normalized);
                if (!isNaN(num)) {
                  const numericString = formatAmount(Math.abs(num));
                  onFormChange({ ...formData, amount: numericString });
                  setAmountDisplay(currencyFormatter.format(Math.abs(num)));
                }
              }}
              placeholder="0.00"
              required
            />
          ) : (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                aria-pressed={formData.isPositive ? 'true' : 'false'}
                onClick={() =>
                  onFormChange({
                    ...formData,
                    isPositive: !formData.isPositive,
                  })
                }
                className={
                  formData.isPositive
                    ? 'border-green-600 text-green-600'
                    : 'border-red-600 text-red-600'
                }
                title={
                  formData.isPositive
                    ? 'Refund (positive)'
                    : 'Expense (negative)'
                }
              >
                {formData.isPositive ? (
                  <Plus className="h-4 w-4" />
                ) : (
                  <Minus className="h-4 w-4" />
                )}
              </Button>
              <Input
                id={`${type}-amount`}
                type="text"
                value={amountDisplay}
                onFocus={() => {
                  setIsAmountFocused(true);
                  if (!amountDisplay) return;
                  if (!amountDisplay.trim().startsWith('=')) {
                    const raw = normalizeNumericString(amountDisplay);
                    setAmountDisplay(raw);
                  }
                }}
                onChange={e => {
                  const rawInput = e.target.value;
                  setAmountDisplay(rawInput);
                  if (rawInput.trim().startsWith('=')) {
                    onFormChange({
                      ...formData,
                      amount: rawInput,
                    });
                  } else {
                    const normalized = normalizeNumericString(rawInput);
                    onFormChange({
                      ...formData,
                      amount: normalized,
                    });
                  }
                }}
                onBlur={e => {
                  setIsAmountFocused(false);
                  const val = e.target.value;
                  if (val.trim().startsWith('=')) {
                    const result = evaluateExpression(val.trim().slice(1));
                    if (result !== null) {
                      const normalized = Math.abs(result); // do not change sign toggle
                      const numericString = formatAmount(normalized);
                      onFormChange({ ...formData, amount: numericString });
                      setAmountDisplay(currencyFormatter.format(normalized));
                    }
                    return;
                  }
                  const normalized = normalizeNumericString(val);
                  const num = parseFloat(normalized);
                  if (!isNaN(num)) {
                    const numericString = formatAmount(Math.abs(num));
                    onFormChange({ ...formData, amount: numericString });
                    setAmountDisplay(currencyFormatter.format(Math.abs(num)));
                  }
                }}
                placeholder="0.00"
                required
              />
            </div>
          )}
        </div>
        <div>
          <Label htmlFor={`${type}-date`}>Date</Label>
          <Input
            id={`${type}-date`}
            type="date"
            value={formData.date}
            onChange={e =>
              onFormChange({
                ...formData,
                date: e.target.value,
              })
            }
            required
          />
        </div>
        <div>
          <Label htmlFor={`${type}-account`}>Account</Label>
          <Select
            value={formData.account_name}
            onValueChange={value =>
              onFormChange({
                ...formData,
                account_name: value,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select account" />
            </SelectTrigger>
            <SelectContent>
              {accounts.map(account => (
                <SelectItem key={account.id} value={String(account.id)}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {!isIncome && (
          <div className="md:col-span-2">
            <Label htmlFor={`${type}-category`}>Category</Label>
            <Select
              value={formData.category || ''}
              onValueChange={value =>
                onFormChange({
                  ...formData,
                  category: value,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map(category => (
                  <SelectItem key={category.id} value={String(category.id)}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between gap-2">
        <div>
          {onDelete && (
            <Button
              type="button"
              variant="outline"
              className="text-red-600 border-red-600 hover:bg-red-50"
              onClick={onDelete}
            >
              Delete
            </Button>
          )}
        </div>
        <div>
          <Button
            type="submit"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {submitLabel ? submitLabel : `Add ${title}`}
          </Button>
        </div>
      </div>
    </form>
  );
}
