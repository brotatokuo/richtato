import { RecategorizeDialog } from '@/components/transactions/RecategorizeDialog';
import { RecategorizeProgressModal } from '@/components/transactions/RecategorizeProgressModal';
import { TransactionTable } from '@/components/transactions/TransactionTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import { DisplayTransaction, transformTransaction } from '@/types/transactions';
import { useEffect, useState } from 'react';

// Main DataTable Component - Transactions Only
export function DataTable() {
  const [transactions, setTransactions] = useState<DisplayTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRecategorizeDialog, setShowRecategorizeDialog] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [recategorizeTaskId, setRecategorizeTaskId] = useState<number | null>(
    null
  );
  const { clearNewCount } = useSyncStatus();

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [transactionsData, categoriesData, accountsData] =
        await Promise.all([
          transactionsApiService.getTransactions(),
          transactionsApiService.getCategories(),
          transactionsApiService.getAccounts(),
        ]);

      // Transform and set data
      setTransactions(transactionsData.map(transformTransaction));
      setAccounts(accountsData);
      setCategories(categoriesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Clear the new transaction count badge when user views this page
    clearNewCount();
  }, [clearNewCount]);

  const handleRecategorize = async (keepExisting: boolean) => {
    setShowRecategorizeDialog(false);

    try {
      const { task_id } =
        await transactionsApiService.startRecategorization(keepExisting);
      setRecategorizeTaskId(task_id);
      setShowProgressModal(true);
    } catch (error) {
      console.error('Error starting recategorization:', error);
      setError(
        error instanceof Error
          ? error.message
          : 'Failed to start recategorization'
      );
    }
  };

  const handleRecategorizeComplete = () => {
    setShowProgressModal(false);
    setRecategorizeTaskId(null);
    loadData(); // Reload transactions to show updated categories
  };

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <div className="w-full max-w-full mx-auto min-w-0">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardContent className="text-center py-8">
              <p className="text-red-600 mb-4">Error loading data: {error}</p>
              <Button onClick={loadData} variant="outline">
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full max-w-full mx-auto space-y-8 sm:space-y-12 min-w-0">
        {/* Main content */}
        <div className="overflow-x-auto min-w-0">
          <div className="min-w-0 max-w-full">
            <TransactionTable
              transactions={transactions}
              onTransactionsChange={setTransactions}
              accounts={accounts}
              categories={categories}
              loading={loading}
              onRefresh={loadData}
              onRecategorizeClick={() => setShowRecategorizeDialog(true)}
            />
          </div>
        </div>
      </div>

      <RecategorizeDialog
        open={showRecategorizeDialog}
        onClose={() => setShowRecategorizeDialog(false)}
        onConfirm={handleRecategorize}
        transactionCount={transactions.length}
      />

      <RecategorizeProgressModal
        open={showProgressModal}
        taskId={recategorizeTaskId}
        onComplete={handleRecategorizeComplete}
      />
    </div>
  );
}
