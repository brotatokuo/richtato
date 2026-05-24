import type { StatementImportResult } from '@/lib/api/statementImport';

export function hasReconciliationWarnings(
  result: StatementImportResult | Record<string, never> | null | undefined
): boolean {
  return Boolean(result && (result.reconciliation_warnings?.length ?? 0) > 0);
}
