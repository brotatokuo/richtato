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
              value={formData.amount}
              onChange={e =>
                onFormChange({
                  ...formData,
                  amount: e.target.value,
                })
              }
              onBlur={e => {
                const val = e.target.value;
                if (val.trim().startsWith('=')) {
                  const result = evaluateExpression(val.trim().slice(1));
                  if (result !== null) {
                    const normalized = Math.abs(result);
                    onFormChange({
                      ...formData,
                      amount: formatAmount(normalized),
                    });
                  }
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
                value={formData.amount}
                onChange={e =>
                  onFormChange({
                    ...formData,
                    amount: e.target.value,
                  })
                }
                onBlur={e => {
                  const val = e.target.value;
                  if (val.trim().startsWith('=')) {
                    const result = evaluateExpression(val.trim().slice(1));
                    if (result !== null) {
                      const normalized = Math.abs(result);
                      onFormChange({
                        ...formData,
                        amount: formatAmount(normalized),
                      });
                    }
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
