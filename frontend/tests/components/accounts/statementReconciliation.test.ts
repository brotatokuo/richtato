import {
  needsOpeningBalanceConfirmation,
  shouldShowReconciliationWarnings,
} from '@/components/accounts/statementReconciliation';
import type { StatementFileRecord } from '@/lib/api/statementFiles';

function makeFile(
  overrides: Partial<StatementFileRecord> = {}
): StatementFileRecord {
  return {
    id: 1,
    account: 1,
    account_name: 'Checking',
    institution: 'bofa',
    statement_period: '2025-06',
    statement_year: 2025,
    statement_month: 6,
    statement_status: 'provisional',
    import_status: 'previewed',
    original_filename: 'stmt.csv',
    content_type: 'text/csv',
    size_bytes: 100,
    file_hash: 'abc',
    parsed_count: 1,
    imported_count: 0,
    duplicate_count: 0,
    invalid_count: 0,
    possible_changed_count: 0,
    last_import_result: {},
    reconciliation_acknowledged_at: null,
    source: 'manual_upload',
    stored_path: 'gdrive://folder-id/stmt.csv',
    drive_file_url: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('shouldShowReconciliationWarnings', () => {
  it('shows warnings when present and not acknowledged', () => {
    expect(
      shouldShowReconciliationWarnings(
        makeFile({
          last_import_result: {
            reconciliation_warnings: ['Balance mismatch'],
          },
        })
      )
    ).toBe(true);
  });

  it('hides warnings after acknowledgement', () => {
    expect(
      shouldShowReconciliationWarnings(
        makeFile({
          last_import_result: {
            reconciliation_warnings: ['Balance mismatch'],
          },
          reconciliation_acknowledged_at: '2026-01-02T00:00:00Z',
        })
      )
    ).toBe(false);
  });
});

describe('needsOpeningBalanceConfirmation', () => {
  it('requires confirmation when create or update is available', () => {
    expect(needsOpeningBalanceConfirmation('available_create')).toBe(true);
    expect(needsOpeningBalanceConfirmation('available_update')).toBe(true);
  });

  it('does not require confirmation for matched or committed actions', () => {
    expect(needsOpeningBalanceConfirmation('matched')).toBe(false);
    expect(needsOpeningBalanceConfirmation('create')).toBe(false);
    expect(needsOpeningBalanceConfirmation('update')).toBe(false);
    expect(needsOpeningBalanceConfirmation('none')).toBe(false);
    expect(needsOpeningBalanceConfirmation(undefined)).toBe(false);
  });
});
