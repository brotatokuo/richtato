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
import { Button } from '@/components/ui/button';
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
import { budgetDashboardApiService } from '@/lib/api/budget-dashboard';
import { CategoryCatalogItem } from '@/lib/api/user';
import { formatCurrency, getCurrencySymbol } from '@/lib/format';
import { TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';

interface BudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: { amount: number }) => Promise<void>;
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
  const [saving, setSaving] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const [avgSpending, setAvgSpending] = useState<number | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (category && isOpen) {
      setAmount(category.budget ? category.budget.amount.toString() : '');
      setShowRemoveConfirm(false);
    }
  }, [category, isOpen]);

  // Fetch historical spending average for this category
  useEffect(() => {
    if (!category || !isOpen) {
      setAvgSpending(null);
      return;
    }

    let cancelled = false;
    setLoadingHistory(true);

    budgetDashboardApiService
      .getBudgetProgressMultiMonth({ months: 6 })
      .then(data => {
        if (cancelled) return;
        const months = data.monthly_data;
        const categorySlug = category.name;
        const categoryDisplay = category.display;

        let totalSpent = 0;
        let monthCount = 0;

        for (const m of months) {
          const cat = m.categories.find(
            c =>
              c.category === categoryDisplay ||
              c.category.toLowerCase().replace(/\s+/g, '-') === categorySlug
          );
          if (cat) {
            totalSpent += cat.spent;
            monthCount++;
          }
        }

        setAvgSpending(
          monthCount > 0 ? Math.round(totalSpent / monthCount) : null
        );
      })
      .catch(() => setAvgSpending(null))
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [category, isOpen]);

  const handleSave = async () => {
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) return;

    setSaving(true);
    try {
      await onSave({ amount: Number(amount) });
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
      setShowRemoveConfirm(false);
    }
  };

  const hasBudget = category?.budget != null;

  return (
    <>
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
                ? `Configure budget for ${category.display}`
                : 'Configure budget for this category'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Spending history hint */}
            {avgSpending !== null && avgSpending > 0 && (
              <div className="flex items-center gap-2 p-2.5 rounded-lg bg-muted/50 border border-border/50">
                <TrendingUp className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div className="text-sm text-muted-foreground">
                  Average spending:{' '}
                  <span className="font-medium text-foreground">
                    {formatCurrency(avgSpending, preferences.currency)}
                  </span>
                  <span className="text-xs">/mo over last 6 months</span>
                </div>
                {!amount && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="ml-auto h-6 text-xs px-2"
                    onClick={() => setAmount(String(avgSpending))}
                  >
                    Use
                  </Button>
                )}
              </div>
            )}
            {loadingHistory && !avgSpending && (
              <div className="text-xs text-muted-foreground animate-pulse">
                Loading spending history...
              </div>
            )}

            {/* Amount */}
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
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            {hasBudget && onRemove && (
              <Button
                type="button"
                variant="destructive"
                onClick={() => setShowRemoveConfirm(true)}
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
              {saving ? 'Saving...' : 'Save Budget'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove confirmation dialog */}
      <AlertDialog open={showRemoveConfirm} onOpenChange={setShowRemoveConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove budget?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the budget for{' '}
              <span className="font-medium text-foreground">
                {category?.display}
              </span>
              . Spending data will be preserved, but you&apos;ll no longer see
              progress tracking for this category.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRemove}
              disabled={saving}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {saving ? 'Removing...' : 'Remove Budget'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
