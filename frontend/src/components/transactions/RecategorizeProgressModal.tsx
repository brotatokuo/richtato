import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { transactionsApiService } from '@/lib/api/transactions';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

interface RecategorizeProgressModalProps {
  open: boolean;
  taskId: number | null;
  onComplete: () => void;
}

interface ProgressData {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total: number;
  processed: number;
  updated: number;
  progress_percent: number;
  error: string | null;
}

export function RecategorizeProgressModal({
  open,
  taskId,
  onComplete,
}: RecategorizeProgressModalProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);

  useEffect(() => {
    if (!taskId || !open) return;

    const pollProgress = async () => {
      try {
        const data =
          await transactionsApiService.getRecategorizeProgress(taskId);
        setProgress(data);

        if (data.status === 'completed' || data.status === 'failed') {
          // Wait 2 seconds to show the final state, then complete
          setTimeout(() => {
            onComplete();
          }, 2000);
        }
      } catch (error) {
        console.error('Error polling progress:', error);
      }
    };

    // Poll immediately
    pollProgress();

    // Then poll every second
    const pollInterval = setInterval(pollProgress, 1000);

    return () => clearInterval(pollInterval);
  }, [taskId, open, onComplete]);

  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Recategorizing Transactions</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {progress ? (
            <>
              <Progress value={progress.progress_percent} className="h-2" />
              <p className="text-sm text-muted-foreground text-center">
                {progress.processed} / {progress.total} transactions processed (
                {Math.round(progress.progress_percent)}%)
              </p>
              <p className="text-xs text-muted-foreground text-center">
                {progress.updated} categories updated
              </p>

              {progress.status === 'completed' && (
                <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
                  <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <AlertDescription className="text-green-800 dark:text-green-200">
                    Recategorization completed successfully!
                  </AlertDescription>
                </Alert>
              )}

              {progress.status === 'failed' && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {progress.error || 'Recategorization failed'}
                  </AlertDescription>
                </Alert>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">
                Initializing recategorization...
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
