import { TransactionsPanel } from '@/components/transactions/TransactionsPanel';
import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

// Main DataTable Component - Transactions Only
export function DataTable() {
  const [searchParams] = useSearchParams();
  const accountId = useMemo(() => {
    const raw = searchParams.get('account');
    if (!raw) return undefined;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : undefined;
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full max-w-full mx-auto space-y-8 sm:space-y-12 min-w-0">
        {/* Main content */}
        <div className="overflow-x-auto min-w-0">
          <div className="min-w-0 max-w-full">
            <TransactionsPanel
              accountId={accountId}
              defaultAccountId={accountId}
              enableRecategorize={!accountId}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
