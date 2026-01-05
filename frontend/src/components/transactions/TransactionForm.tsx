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
import { usePreferences } from '@/contexts/PreferencesContext';
import { Account, Category } from '@/lib/api/transactions';
import { TransactionFormData } from '@/types/transactions';
import { Calendar, Minus, Plus } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface TransactionFormProps {
  formData: TransactionFormData;
  onFormChange: (data: TransactionFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  accounts: Account[];
  categories: Category[];
  submitLabel?: string;
  onDelete?: () => void;
}

export function TransactionForm({
  formData,
  onFormChange,
  onSubmit,
  accounts,
  categories,
  submitLabel,
  onDelete,
}: TransactionFormProps) {
  const { preferences, getCurrencySymbol } = usePreferences();
  const isCredit = formData.transactionType === 'credit';
  const title = isCredit ? 'Income' : 'Expense';
  const placeholder = isCredit
    ? 'e.g., Salary, Freelance work'
    : 'e.g., Groceries, Gas, Coffee';

  // Show all categories for maximum flexibility
  // Users can select any category regardless of transaction type
  const filteredCategories = categories;

  // Create number formatter for displaying amounts (without currency symbol)
  const numberFormatter = new Intl.NumberFormat('en-US', {
    style: 'decimal',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });

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
    // Remove common currency symbols, commas, and spaces
    return val.replace(/[,$€£¥₹\s]/g, '');
  };

  const [amountDisplay, setAmountDisplay] = useState<string>(
    formData.amount || ''
  );
  const [isAmountFocused, setIsAmountFocused] = useState<boolean>(false);
  const dateInputRef = useRef<HTMLInputElement>(null);

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
          const formatter = new Intl.NumberFormat('en-US', {
            style: 'decimal',
            maximumFractionDigits: 2,
            minimumFractionDigits: 2,
          });
          setAmountDisplay(formatter.format(Math.abs(num)));
        } else {
          setAmountDisplay(formData.amount);
        }
      }
    }
  }, [formData.amount, isAmountFocused]);

  // Reset category when transaction type changes (to avoid invalid category)
  const handleTransactionTypeToggle = () => {
    const newType = isCredit ? 'debit' : 'credit';
    onFormChange({
      ...formData,
      transactionType: newType,
      category: '', // Reset category when type changes
    });
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="transaction-description">Description</Label>
          <Input
            id="transaction-description"
            value={formData.description}
            onChange={e =>
              onFormChange({
                ...formData,
                description: e.target.value,
              })
            }
            onBlur={e => {
              const val = e.target.value || '';
              const hasRefundWord = /\brefund\b/i.test(val);
              // Flip to credit if "refund" is mentioned in expense mode
              if (hasRefundWord && formData.transactionType === 'debit') {
                onFormChange({
                  ...formData,
                  transactionType: 'credit',
                  category: '', // Reset category
                });
              }
            }}
            placeholder={placeholder}
            required
          />
        </div>
        <div>
          <Label htmlFor="transaction-amount">Amount</Label>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              aria-pressed={isCredit ? 'true' : 'false'}
              onClick={handleTransactionTypeToggle}
              className={
                isCredit
                  ? 'border-green-600 text-green-600'
                  : 'border-red-600 text-red-600'
              }
              title={isCredit ? 'Income (credit)' : 'Expense (debit)'}
            >
              {isCredit ? (
                <Plus className="h-4 w-4" />
              ) : (
                <Minus className="h-4 w-4" />
              )}
            </Button>
            <span className="text-sm font-medium text-muted-foreground px-3 py-2 bg-muted rounded-md border border-input">
              {getCurrencySymbol(preferences.currency || 'USD')}
            </span>
            <Input
              id="transaction-amount"
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
                    const normalized = Math.abs(result);
                    const numericString = formatAmount(normalized);
                    onFormChange({ ...formData, amount: numericString });
                    setAmountDisplay(numberFormatter.format(normalized));
                  }
                  return;
                }
                const normalized = normalizeNumericString(val);
                const num = parseFloat(normalized);
                if (!isNaN(num)) {
                  const numericString = formatAmount(Math.abs(num));
                  onFormChange({ ...formData, amount: numericString });
                  setAmountDisplay(numberFormatter.format(Math.abs(num)));
                }
              }}
              placeholder="0.00"
              required
            />
          </div>
        </div>
        <div>
          <Label htmlFor="transaction-date">Date</Label>
          <div className="flex items-center gap-2">
            <Input
              ref={dateInputRef}
              id="transaction-date"
              type="date"
              value={formData.date}
              onChange={e =>
                onFormChange({
                  ...formData,
                  date: e.target.value,
                })
              }
              className="flex-1"
              required
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => dateInputRef.current?.showPicker?.()}
              title="Open calendar"
            >
              <Calendar className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <Label htmlFor="transaction-account">Account</Label>
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
        <div className="md:col-span-2">
          <Label htmlFor="transaction-category">Category</Label>
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
              {filteredCategories.map(category => (
                <SelectItem key={category.id} value={String(category.id)}>
                  {category.full_path || category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="md:col-span-2">
          <Label htmlFor="transaction-notes">Notes (optional)</Label>
          <textarea
            id="transaction-notes"
            value={formData.notes ?? ''}
            onChange={e =>
              onFormChange({
                ...formData,
                notes: e.target.value,
              })
            }
            placeholder="Add details, reminders, or context"
            className="flex min-h-[96px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
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
