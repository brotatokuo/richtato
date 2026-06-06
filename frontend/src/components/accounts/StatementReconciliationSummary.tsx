import type { StatementImportResult } from '@/lib/api/statementImport';
import { formatCurrency, formatDate } from '@/lib/format';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface StatementReconciliationSummaryProps {
  result: Pick<
    StatementImportResult,
    'balance_summary' | 'reconciliation' | 'reconciliation_warnings'
  >;
  compact?: boolean;
}

const MAX_VISIBLE_RECONCILIATION_WARNINGS = 5;

export function StatementReconciliationSummary({
  result,
  compact = false,
}: StatementReconciliationSummaryProps) {
  const warnings = Array.from(new Set(result.reconciliation_warnings ?? []));
  const summary = result.balance_summary;
  const reconciliation = result.reconciliation ?? {};
  const hasWarnings = warnings.length > 0;
  const visibleWarnings = warnings.slice(
    0,
    MAX_VISIBLE_RECONCILIATION_WARNINGS
  );
  const hiddenWarningCount = Math.max(
    0,
    warnings.length - visibleWarnings.length
  );
  const isBalanced =
    !hasWarnings &&
    (reconciliation.statement_internal_ok === true ||
      reconciliation.account_ending_ok === true);
  const openingAction = reconciliation.opening_balance_action;

  if (!summary && warnings.length === 0) {
    return null;
  }

  const formatBalance = (value: string | undefined) => {
    if (!value) return '—';
    const parsed = Number(value.replace(/,/g, ''));
    if (Number.isNaN(parsed)) return `$${value}`;
    return formatCurrency(parsed);
  };

  const openingBalanceMessage = (() => {
    if (!openingAction || openingAction === 'none') return null;

    if (openingAction === 'matched') {
      return 'Account opening balance matches statement beginning balance.';
    }

    if (
      openingAction === 'available_create' ||
      openingAction === 'available_update'
    ) {
      return 'Statement beginning balance differs from account opening balance. Choose whether to update before importing.';
    }

    if (openingAction === 'create' || openingAction === 'update') {
      return `Account opening balance ${openingAction === 'create' ? 'set' : 'updated'} to ${formatBalance(reconciliation.opening_balance_amount)}${
        reconciliation.opening_balance_date
          ? ` on ${formatDate(reconciliation.opening_balance_date)}`
          : ''
      }.`;
    }

    return null;
  })();

  return (
    <div
      className={
        compact
          ? 'space-y-1'
          : 'rounded-lg border border-border bg-muted/20 p-3 text-sm'
      }
    >
      {!compact && (
        <div className="flex items-center gap-2">
          {hasWarnings ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : isBalanced ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : null}
          <p className="font-medium text-foreground">Balance reconciliation</p>
        </div>
      )}

      {summary && (
        <div
          className={
            compact
              ? 'text-[11px] text-muted-foreground/80'
              : 'mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground'
          }
        >
          <span>Beginning: {formatBalance(summary.beginning_balance)}</span>
          <span>Ending: {formatBalance(summary.ending_balance)}</span>
        </div>
      )}

      {openingBalanceMessage && (
        <p
          className={
            compact
              ? 'text-[11px] text-muted-foreground/80'
              : 'mt-2 text-xs text-muted-foreground'
          }
        >
          {openingBalanceMessage}
        </p>
      )}

      {warnings.length > 0 && (
        <ul
          className={
            compact
              ? 'mt-1 max-h-32 space-y-1 overflow-y-auto scrollbar-thin text-[11px] text-amber-700 dark:text-amber-300'
              : 'mt-2 max-h-40 space-y-1 overflow-y-auto scrollbar-thin text-xs text-amber-700 dark:text-amber-300'
          }
        >
          {visibleWarnings.map((warning, index) => (
            <li key={`${index}-${warning}`}>{warning}</li>
          ))}
          {hiddenWarningCount > 0 && (
            <li className="text-muted-foreground">
              ... and {hiddenWarningCount} more warning
              {hiddenWarningCount === 1 ? '' : 's'}.
            </li>
          )}
        </ul>
      )}

      {!compact &&
        !hasWarnings &&
        reconciliation.account_ending_ok === true && (
          <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">
            Account balance matches the statement ending balance.
          </p>
        )}
    </div>
  );
}
