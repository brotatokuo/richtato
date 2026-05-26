import {
  getStatementFileUrl,
  isDriveStatementFile,
} from '@/lib/statementFileUrl';
import type { StatementFileRecord } from '@/lib/api/statementFiles';

describe('statementFileUrl', () => {
  const baseFile: StatementFileRecord = {
    id: 42,
    account: 1,
    account_name: 'Checking',
    institution: 'bofa',
    statement_period: '2026-05',
    statement_year: 2026,
    statement_month: 5,
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
    stored_path: 'gdrive://folder-id/abc-stmt.csv',
    drive_file_url: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  it('prefers the Drive URL when present', () => {
    expect(
      getStatementFileUrl({
        ...baseFile,
        drive_file_url: 'https://drive.google.com/file/d/abc/view',
      })
    ).toBe('https://drive.google.com/file/d/abc/view');
  });

  it('falls back to the download endpoint', () => {
    expect(getStatementFileUrl(baseFile)).toBe(
      '/api/v1/accounts/statements/42/download/'
    );
  });

  it('detects Drive-backed files from stored_path', () => {
    expect(isDriveStatementFile(baseFile)).toBe(true);
  });
});
