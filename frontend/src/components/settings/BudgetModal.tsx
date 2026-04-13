import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePreferences } from '@/contexts/PreferencesContext';
import { getCurrencySymbol } from '@/lib/format';
import { CategoryCatalogItem } from '@/lib/api/user';
import { ChevronDown } from 'lucide-react';
import { useState, useEffect } from 'react';

interface BudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    amount: number;
    start_date: string;
    end_date: string | null;
  }) => Promise<void>;
  onRemove?: () => Promise<void>;
  category: CategoryCatalogItem | null;
  loading?: boolean;
}

export function BudgetModal({
  isOpen,
  onClose,
  onSave,
  onRemove,
  category,
  loading = false,
}: BudgetModalProps) {
  const { preferences } = usePreferences();
  const currencySymbol = getCurrencySymbol(preferences.currency);

  const [amount, setAmount] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [saving, setSaving] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  // Reset form when category changes or modal opens
  useEffect(() => {
    if (category && isOpen) {
      if (category.budget) {
        setAmount(category.budget.amount.toString());
        setStartDate(category.budget.start_date);
        setEndDate(category.budget.end_date || '');
        // Open advanced section if a non-default date range is set
        setAdvancedOpen(
          !!category.budget.end_date ||
            category.budget.start_date !==
              new Date(new Date().getFullYear(), new Date().getMonth(), 1)
                .toISOString()
                .slice(0, 10)
        );
      } else {
        const today = new Date();
        const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        setAmount('');
        setStartDate(firstOfMonth.toISOString().slice(0, 10));
        setEndDate('');
        setAdvancedOpen(false);
      }
    }
  }, [category, isOpen]);

  const handleSave = async () => {
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) return;

    setSaving(true);
    try {
      await onSave({
        amount: Number(amount),
        start_date: startDate,
        end_date: endDate || null,
      });
      onClose();
    } catch {
      // Error handling is done by parent
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    if (!onRemove) return;
    setSaving(true);
    try {
      await onRemove();
      onClose();
    } catch {
      // Error handling is done by parent
    } finally {
      setSaving(false);
    }
  };

  const hasBudget = category?.budget != null;

  return (
    <Dialog open={isOpen} onOpenChange={open => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {category && (
              <span className="text-xl" aria-hidden>
                {category.icon}
              </span>
            )}
            {hasBudget ? 'Edit Budget' : 'Set Budget'}
          </DialogTitle>
          <DialogDescription>
            {category
              ? `Configure monthly budget for ${category.display}`
              : 'Configure budget for this category'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Amount — primary field */}
          <div className="space-y-2">
            <Label htmlFor="budget-amount">Monthly Amount</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground select-none">
                {currencySymbol}
              </span>
              <Input
                id="budget-amount"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                className="pl-7"
                autoFocus
              />
            </div>
          </div>

          {/* Advanced date range — collapsed by default */}
          <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ChevronDown
                  className={`h-4 w-4 transition-transform duration-200 ${advancedOpen ? 'rotate-180' : ''}`}
                />
                Advanced: date range
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 pt-3">
              <div className="space-y-2">
                <Label htmlFor="budget-start">Start Date</Label>
                <Input
                  id="budget-start"
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="budget-end">
                  End Date{' '}
                  <span className="text-muted-foreground font-normal">
                    (optional)
                  </span>
                </Label>
                <Input
                  id="budget-end"
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  placeholder="Never expires"
                />
                <p className="text-xs text-muted-foreground">
                  Leave empty for an ongoing monthly budget
                </p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          {hasBudget && onRemove && (
            <Button
              type="button"
              variant="destructive"
              onClick={handleRemove}
              disabled={saving || loading}
              className="sm:mr-auto"
            >
              Remove Budget
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={saving || loading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSave}
            disabled={
              saving ||
              loading ||
              !amount ||
              isNaN(Number(amount)) ||
              Number(amount) <= 0
            }
          >
            {saving ? 'Saving…' : 'Save Budget'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
