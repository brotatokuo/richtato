import type { StatementImportResult } from '@/lib/api/statementImport';
import type { StatementFileRecord } from '@/lib/api/statementFiles';

export type OpeningBalanceAction = NonNullable<
  NonNullable<StatementImportResult['reconciliation']>['opening_balance_action']
>;

export function hasReconciliationWarnings(
  result: StatementImportResult | Record<string, never> | null | undefined
): boolean {
  return Boolean(result && (result.reconciliation_warnings?.length ?? 0) > 0);
}

export function needsOpeningBalanceConfirmation(
  action: OpeningBalanceAction | undefined
): boolean {
  return action === 'available_create' || action === 'available_update';
}

export function shouldShowReconciliationWarnings(
  file: Pick<
    StatementFileRecord,
    'last_import_result' | 'reconciliation_acknowledged_at'
  >
): boolean {
  return (
    hasReconciliationWarnings(file.last_import_result) &&
    !file.reconciliation_acknowledged_at
  );
}
