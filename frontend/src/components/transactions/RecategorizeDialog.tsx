import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle } from 'lucide-react';
import { useState } from 'react';

interface RecategorizeDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (keepExisting: boolean) => void;
  transactionCount: number;
}

export function RecategorizeDialog({
  open,
  onClose,
  onConfirm,
  transactionCount,
}: RecategorizeDialogProps) {
  const [keepExisting, setKeepExisting] = useState('keep');

  const handleConfirm = () => {
    onConfirm(keepExisting === 'keep');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Recategorize All Transactions?</DialogTitle>
          <DialogDescription>
            This will recategorize all {transactionCount} transactions using
            your current keyword rules.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This action cannot be undone. All transaction categories will be
              updated based on your current keywords.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="unmatch-behavior">
              For transactions with no keyword match:
            </Label>
            <Select value={keepExisting} onValueChange={setKeepExisting}>
              <SelectTrigger id="unmatch-behavior">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="keep">Keep existing category</SelectItem>
                <SelectItem value="uncategorize">
                  Mark as uncategorized
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleConfirm}>Recategorize All</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
