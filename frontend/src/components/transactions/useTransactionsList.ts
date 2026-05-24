import {
  Account,
  Category,
  transactionsApiService,
} from '@/lib/api/transactions';
import { DisplayTransaction, transformTransaction } from '@/types/transactions';
import { useCallback, useEffect, useState } from 'react';

const DEFAULT_PAGE_SIZE = 50;

export interface UseTransactionsListOptions {
  accountId?: number;
  categoryId?: number;
  startDate?: string;
  endDate?: string;
  type?: 'debit' | 'credit';
  scope?: 'personal' | 'household';
  pageSize?: number;
  enabled?: boolean;
}

export function useTransactionsList({
  accountId,
  categoryId,
  startDate,
  endDate,
  type,
  scope,
  pageSize = DEFAULT_PAGE_SIZE,
  enabled = true,
}: UseTransactionsListOptions = {}) {
  const [transactions, setTransactions] = useState<DisplayTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(enabled);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const loadInitialData = useCallback(async () => {
    if (!enabled) return;

    try {
      setLoading(true);
      setError(null);

      const [transactionsRes, categoriesData, accountsData] = await Promise.all(
        [
          transactionsApiService.getTransactions({
            page: 1,
            pageSize,
            accountId,
            categoryId,
            startDate,
            endDate,
            type,
            scope,
          }),
          transactionsApiService.getCategories(),
          transactionsApiService.getAccounts({ scope }),
        ]
      );

      setTransactions(transactionsRes.transactions.map(transformTransaction));
      setAccounts(accountsData);
      setCategories(categoriesData);
      setPage(1);
      setHasNext(transactionsRes.has_next ?? false);
      setTotalCount(
        transactionsRes.total_count ?? transactionsRes.transactions.length
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [
    accountId,
    categoryId,
    enabled,
    endDate,
    pageSize,
    scope,
    startDate,
    type,
  ]);

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasNext || !enabled) return;

    try {
      setLoadingMore(true);
      const nextPage = page + 1;
      const res = await transactionsApiService.getTransactions({
        page: nextPage,
        pageSize,
        accountId,
        categoryId,
        startDate,
        endDate,
        type,
        scope,
      });
      setTransactions(prev => [
        ...prev,
        ...res.transactions.map(transformTransaction),
      ]);
      setPage(nextPage);
      setHasNext(res.has_next ?? false);
    } finally {
      setLoadingMore(false);
    }
  }, [
    accountId,
    categoryId,
    enabled,
    endDate,
    hasNext,
    loadingMore,
    page,
    pageSize,
    scope,
    startDate,
    type,
  ]);

  useEffect(() => {
    if (enabled) {
      loadInitialData();
    }
  }, [enabled, loadInitialData]);

  return {
    transactions,
    setTransactions,
    accounts,
    categories,
    loading,
    loadingMore,
    error,
    hasNext,
    totalCount,
    loadData: loadInitialData,
    loadMore,
  };
}
