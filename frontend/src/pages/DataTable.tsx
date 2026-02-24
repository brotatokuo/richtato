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
import { useCallback, useEffect, useState } from 'react';

const PAGE_SIZE = 50;

// Main DataTable Component - Transactions Only
export function DataTable() {
  const [transactions, setTransactions] = useState<DisplayTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [showRecategorizeDialog, setShowRecategorizeDialog] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [recategorizeTaskId, setRecategorizeTaskId] = useState<number | null>(
    null
  );
  const { clearNewCount } = useSyncStatus();

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [transactionsRes, categoriesData, accountsData] =
        await Promise.all([
          transactionsApiService.getTransactions({
            page: 1,
            pageSize: PAGE_SIZE,
          }),
          transactionsApiService.getCategories(),
          transactionsApiService.getAccounts(),
        ]);

      setTransactions(
        transactionsRes.transactions.map(transformTransaction)
      );
      setAccounts(accountsData);
      setCategories(categoriesData);
      setPage(1);
      setHasNext(transactionsRes.has_next ?? false);
      setTotalCount(transactionsRes.total_count ?? transactionsRes.transactions.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasNext) return;
    try {
      setLoadingMore(true);
      const nextPage = page + 1;
      const res = await transactionsApiService.getTransactions({
        page: nextPage,
        pageSize: PAGE_SIZE,
      });
      const newTxns = res.transactions.map(transformTransaction);
      setTransactions(prev => [...prev, ...newTxns]);
      setPage(nextPage);
      setHasNext(res.has_next ?? false);
    } catch (err) {
      console.error('Error loading more:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [page, hasNext, loadingMore]);

  const loadData = useCallback(async () => {
    await loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    loadInitialData();
    clearNewCount();
  }, [loadInitialData, clearNewCount]);

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
              loadingMore={loadingMore}
              hasMore={hasNext}
              totalCount={totalCount}
              onLoadMore={loadMore}
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
        transactionCount={totalCount || transactions.length}
      />

      <RecategorizeProgressModal
        open={showProgressModal}
        taskId={recategorizeTaskId}
        onComplete={handleRecategorizeComplete}
      />
    </div>
  );
}
