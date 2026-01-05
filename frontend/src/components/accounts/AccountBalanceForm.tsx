import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Calendar } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface AccountBalanceFormProps {
  accountId: number;
  accountName: string;
  initialData?: { balance: string | number; date: string; id?: number };
  onSubmit: (data: { balance: number; date: string; id?: number }) => Promise<void>;
  onDelete?: () => Promise<void>;
  onCancel: () => void;
}

export function AccountBalanceForm({
  accountId: _accountId,
  accountName,
  initialData,
  onSubmit,
  onDelete,
  onCancel,
}: AccountBalanceFormProps) {
  const { preferences, getCurrencySymbol } = usePreferences();
  const [balance, setBalance] = useState(
    initialData?.balance ? String(initialData.balance) : ''
  );
  const [date, setDate] = useState(initialData?.date || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Create number formatter for displaying amounts
  const numberFormatter = new Intl.NumberFormat('en-US', {
    style: 'decimal',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });

  const [balanceDisplay, setBalanceDisplay] = useState<string>(balance || '');
  const [isBalanceFocused, setIsBalanceFocused] = useState<boolean>(false);

  useEffect(() => {
    if (!date) {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      setDate(`${year}-${month}-${day}`);
    }
    // Only run on mount - intentionally not depending on date
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!isBalanceFocused && balance) {
      const balanceStr = String(balance);
      const num = parseFloat(balanceStr.replace(/[,$€£¥₹\s]/g, ''));
      if (!isNaN(num)) {
        const formatter = new Intl.NumberFormat('en-US', {
          style: 'decimal',
          maximumFractionDigits: 2,
          minimumFractionDigits: 2,
        });
        setBalanceDisplay(formatter.format(Math.abs(num)));
      }
    }
  }, [balance, isBalanceFocused]);

  const normalizeNumericString = (val: string): string => {
    return val.replace(/[,$€£¥₹\s]/g, '');
  };

  const formatAmount = (value: number): string => {
    return (Math.round(value * 100) / 100).toFixed(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!balance || !date) return;

    setIsSubmitting(true);
    try {
      const normalized = normalizeNumericString(balance);
      const balanceNum = parseFloat(normalized);
      if (isNaN(balanceNum)) {
        alert('Please enter a valid number for balance');
        return;
      }

      await onSubmit({
        balance: balanceNum,
        date,
        ...(initialData?.id ? { id: initialData.id } : {}),
      });
    } catch (error) {
      console.error('Error submitting balance:', error);
      alert('Failed to save balance. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4">
        <div>
          <Label htmlFor="account-name">Account</Label>
          <Input
            id="account-name"
            value={accountName}
            disabled
            className="bg-muted"
          />
        </div>

        <div>
          <Label htmlFor="balance">Balance</Label>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground px-3 py-2 bg-muted rounded-md border border-input">
              {getCurrencySymbol(preferences.currency || 'USD')}
            </span>
            <Input
              id="balance"
              type="text"
              value={balanceDisplay}
              onFocus={() => {
                setIsBalanceFocused(true);
                if (balanceDisplay) {
                  const raw = normalizeNumericString(balanceDisplay);
                  setBalanceDisplay(raw);
                }
              }}
              onChange={e => {
                const rawInput = e.target.value;
                setBalanceDisplay(rawInput);
                const normalized = normalizeNumericString(rawInput);
                setBalance(normalized);
              }}
              onBlur={e => {
                setIsBalanceFocused(false);
                const val = e.target.value;
                const normalized = normalizeNumericString(val);
                const num = parseFloat(normalized);
                if (!isNaN(num)) {
                  const numericString = formatAmount(num);
                  setBalance(numericString);
                  setBalanceDisplay(numberFormatter.format(num));
                }
              }}
              placeholder="0.00"
              required
            />
          </div>
        </div>

        <div>
          <Label htmlFor="date">Date</Label>
          <div className="flex items-center gap-2">
            <Input
              ref={dateInputRef}
              id="date"
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
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
      </div>

      <div className="flex items-center justify-between gap-2 pt-4">
        <div>
          {onDelete && initialData?.id && (
            <Button
              type="button"
              variant="outline"
              className="text-red-600 border-red-600 hover:bg-red-50"
              onClick={onDelete}
              disabled={isSubmitting}
            >
              Delete
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Saving...' : initialData?.id ? 'Update' : 'Add'}
          </Button>
        </div>
      </div>
    </form>
  );
}
