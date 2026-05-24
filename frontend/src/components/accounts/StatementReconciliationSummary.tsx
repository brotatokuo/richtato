import type { StatementImportResult } from '@/lib/api/statementImport';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface StatementReconciliationSummaryProps {
  result: Pick<
    StatementImportResult,
    'balance_summary' | 'reconciliation' | 'reconciliation_warnings'
  >;
  compact?: boolean;
}

export function StatementReconciliationSummary({
  result,
  compact = false,
}: StatementReconciliationSummaryProps) {
  const warnings = result.reconciliation_warnings ?? [];
  const summary = result.balance_summary;
  const reconciliation = result.reconciliation ?? {};
  const hasWarnings = warnings.length > 0;
  const isBalanced =
    !hasWarnings &&
    (reconciliation.statement_internal_ok === true ||
      reconciliation.account_ending_ok === true);

  if (!summary && warnings.length === 0) {
    return null;
  }

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
          <span>Beginning: ${summary.beginning_balance}</span>
          <span>Ending: ${summary.ending_balance}</span>
        </div>
      )}

      {reconciliation.opening_balance_action &&
        ['create', 'update', 'will_create', 'will_update'].includes(
          reconciliation.opening_balance_action
        ) && (
          <p
            className={
              compact
                ? 'text-[11px] text-muted-foreground/80'
                : 'mt-2 text-xs text-muted-foreground'
            }
          >
            Opening balance{' '}
            {reconciliation.opening_balance_action.startsWith('will_')
              ? 'will be set'
              : 'set'}{' '}
            to ${reconciliation.opening_balance_amount}
            {reconciliation.opening_balance_date
              ? ` on ${reconciliation.opening_balance_date}`
              : ''}
            .
          </p>
        )}

      {warnings.length > 0 && (
        <ul
          className={
            compact
              ? 'mt-1 space-y-1 text-[11px] text-amber-700 dark:text-amber-300'
              : 'mt-2 space-y-1 text-xs text-amber-700 dark:text-amber-300'
          }
        >
          {warnings.map(warning => (
            <li key={warning}>{warning}</li>
          ))}
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
