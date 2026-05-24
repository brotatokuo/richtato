import { csrfService } from './csrf';
import type { StatementImportResult } from './statementImport';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export type StatementStatus = 'provisional' | 'closed';
export type StatementFileImportStatus =
  | 'uploaded'
  | 'previewed'
  | 'imported'
  | 'failed';
export type StatementFileSource = 'manual_upload' | 'agent_drop' | 'unknown';

export interface StatementFileRecord {
  id: number;
  account: number;
  account_name: string;
  institution: string;
  statement_period: string;
  statement_year: number;
  statement_month: number;
  statement_status: StatementStatus;
  import_status: StatementFileImportStatus;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  file_hash: string;
  parsed_count: number;
  imported_count: number;
  duplicate_count: number;
  invalid_count: number;
  possible_changed_count: number;
  last_import_result: StatementImportResult | Record<string, never>;
  reconciliation_acknowledged_at: string | null;
  source: StatementFileSource;
  stored_path: string;
  drive_file_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StatementFolderMonth {
  month: number;
  count: number;
}

export interface StatementFolderYear {
  year: number;
  months: StatementFolderMonth[];
  count: number;
}

export interface StatementFolderAccount {
  account_id: number;
  account_name: string;
  years: StatementFolderYear[];
  count: number;
}

export interface StatementFileListResponse {
  rows: StatementFileRecord[];
  tree: StatementFolderAccount[];
}

export interface StatementFileActionResponse {
  statement: StatementFileRecord;
  result: StatementImportResult;
}

export interface StatementFileUploadInput {
  file: File;
  account: number;
  institution: string;
  statementPeriod?: string;
  statementStatus: StatementStatus;
  statementYear?: number;
  statementMonth?: number;
}

class StatementFileService {
  async list(input?: {
    account?: number;
    year?: number;
    month?: number;
    institution?: string;
    importStatus?: StatementFileImportStatus;
  }): Promise<StatementFileListResponse> {
    const url = new URL(
      `${API_BASE}/accounts/statements/`,
      window.location.origin
    );
    if (input?.account) url.searchParams.set('account', String(input.account));
    if (input?.year) url.searchParams.set('year', String(input.year));
    if (input?.month) url.searchParams.set('month', String(input.month));
    if (input?.institution)
      url.searchParams.set('institution', input.institution);
    if (input?.importStatus)
      url.searchParams.set('import_status', input.importStatus);

    const response = await fetch(url.toString(), {
      method: 'GET',
      credentials: 'include',
    });
    return this.handleResponse<StatementFileListResponse>(response);
  }

  async upload(input: StatementFileUploadInput): Promise<{
    statement: StatementFileRecord;
    created: boolean;
  }> {
    const formData = new FormData();
    formData.append('file', input.file);
    formData.append('account', String(input.account));
    formData.append('institution', input.institution);
    formData.append('statement_period', input.statementPeriod ?? '');
    formData.append('statement_status', input.statementStatus);
    if (input.statementYear)
      formData.append('statement_year', String(input.statementYear));
    if (input.statementMonth)
      formData.append('statement_month', String(input.statementMonth));

    const response = await this.fetchWithCsrf(
      `${API_BASE}/accounts/statements/`,
      {
        method: 'POST',
        body: formData,
      }
    );
    return this.handleResponse(response);
  }

  async update(
    id: number,
    input: Partial<{
      account: number;
      institution: string;
      statement_period: string;
      statement_status: StatementStatus;
      statement_year: number;
      statement_month: number;
      reconciliation_acknowledged: boolean;
    }>
  ): Promise<StatementFileRecord> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/statements/${id}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(input),
      }
    );
    return this.handleResponse(response);
  }

  async remove(id: number): Promise<void> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/statements/${id}/`,
      { method: 'DELETE' }
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to delete statement');
    }
  }

  async acknowledgeReconciliation(id: number): Promise<StatementFileRecord> {
    return this.update(id, { reconciliation_acknowledged: true });
  }

  async preview(id: number): Promise<StatementFileActionResponse> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/statements/${id}/preview/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async import(
    id: number,
    options?: { applyOpeningBalance?: boolean }
  ): Promise<StatementFileActionResponse> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/statements/${id}/import/`,
      {
        method: 'POST',
        body: JSON.stringify({
          apply_opening_balance: Boolean(options?.applyOpeningBalance),
        }),
      }
    );
    return this.handleResponse(response);
  }

  getDownloadUrl(id: number): string {
    return `${API_BASE}/accounts/statements/${id}/download/`;
  }

  async scanAccount(accountId: number): Promise<{
    files_seen: number;
    files_imported: number;
    files_skipped: number;
    files_failed: number;
    files_removed: number;
    outcomes: {
      relative_path: string;
      status: string;
      detail: string;
      imported_count: number;
    }[];
  }> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/${accountId}/scan/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  private async fetchWithCsrf(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    const csrfToken = await csrfService.getCSRFToken();
    let response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        ...(options.headers ?? {}),
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
      },
    });

    if (response.status === 403) {
      const refreshedToken = await csrfService.refreshToken();
      response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          ...(options.headers ?? {}),
          'X-CSRFToken': refreshedToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
    }

    return response;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`
      );
    }
    return response.json();
  }
}

export const statementFileService = new StatementFileService();
