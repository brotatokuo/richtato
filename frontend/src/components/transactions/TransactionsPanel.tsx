import { RecategorizeDialog } from '@/components/transactions/RecategorizeDialog';
import { RecategorizeProgressModal } from '@/components/transactions/RecategorizeProgressModal';
import { TransactionTable } from '@/components/transactions/TransactionTable';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { transactionsApiService } from '@/lib/api/transactions';
import { DisplayTransaction } from '@/types/transactions';
import { useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  useTransactionsList,
  UseTransactionsListOptions,
} from './useTransactionsList';

interface TransactionsPanelProps extends UseTransactionsListOptions {
  defaultAccountId?: number;
  hiddenColumns?: Array<keyof DisplayTransaction>;
  enableRecategorize?: boolean;
  className?: string;
}

export function TransactionsPanel({
  defaultAccountId,
  hiddenColumns,
  enableRecategorize = false,
  className,
  ...listOptions
}: TransactionsPanelProps) {
  const {
    transactions,
    setTransactions,
    accounts,
    categories,
    loading,
    loadingMore,
    error,
    hasNext,
    totalCount,
    loadData,
    loadMore,
  } = useTransactionsList(listOptions);

  const [showRecategorizeDialog, setShowRecategorizeDialog] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [recategorizeTaskId, setRecategorizeTaskId] = useState<number | null>(
    null
  );

  const filterScope = useMemo(
    () => ({
      accountId: listOptions.accountId,
      categoryId: listOptions.categoryId,
      startDate: listOptions.startDate,
      endDate: listOptions.endDate,
      type: listOptions.type,
    }),
    [
      listOptions.accountId,
      listOptions.categoryId,
      listOptions.endDate,
      listOptions.startDate,
      listOptions.type,
    ]
  );

  const handleRecategorize = async (keepExisting: boolean) => {
    setShowRecategorizeDialog(false);

    try {
      const { task_id } =
        await transactionsApiService.startRecategorization(keepExisting);
      setRecategorizeTaskId(task_id);
      setShowProgressModal(true);
    } catch (error) {
      toast.error('Failed to start recategorization', {
        description: error instanceof Error ? error.message : undefined,
      });
    }
  };

  const handleRecategorizeComplete = () => {
    setShowProgressModal(false);
    setRecategorizeTaskId(null);
    loadData();
  };

  if (error) {
    return (
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="text-center py-8">
          <p className="text-red-600 mb-4">Error loading data: {error}</p>
          <Button onClick={loadData} variant="outline">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={className}>
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
        onRecategorizeClick={
          enableRecategorize ? () => setShowRecategorizeDialog(true) : undefined
        }
        defaultAccountId={defaultAccountId}
        hiddenColumns={hiddenColumns}
        filterScope={filterScope}
      />

      {enableRecategorize && (
        <>
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
        </>
      )}
    </div>
  );
}
