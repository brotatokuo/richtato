import { csrfService } from './csrf';
import { fetchWithAuth } from './fetchClient';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface BackupImportCounts {
  categories: number;
  budgets: number;
  accounts: number;
  transactions: number;
}

export interface BackupImportPreview {
  valid: boolean;
  can_import: boolean;
  errors: string[];
  warnings: string[];
  counts: BackupImportCounts;
  source_profile: {
    username: string;
    email: string;
  };
}

export interface BackupImportStatus {
  can_import: boolean;
  reason: string | null;
}

export interface BackupImportResult {
  imported: BackupImportCounts & {
    keywords: number;
    budget_allocations: number;
  };
}

export interface TransactionCsvFilters {
  startDate?: string;
  endDate?: string;
  accountId?: number;
}

class UserBackupApi {
  private async fetchWithCsrf(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    const csrfToken = await csrfService.getCSRFToken();
    let response = await fetchWithAuth(url, {
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
      response = await fetchWithAuth(url, {
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

  private async handleJsonResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const message =
        typeof errorData.error === 'string'
          ? errorData.error
          : `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }
    return response.json() as Promise<T>;
  }

  private triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async getImportStatus(): Promise<BackupImportStatus> {
    const response = await fetchWithAuth(
      `${API_BASE}/auth/backup/import/status/`,
      {
        credentials: 'include',
      }
    );
    return this.handleJsonResponse<BackupImportStatus>(response);
  }

  async downloadJsonBackup(): Promise<void> {
    const response = await fetchWithAuth(`${API_BASE}/auth/backup/export/`, {
      credentials: 'include',
    });
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      throw new Error(
        typeof errorData.error === 'string'
          ? errorData.error
          : `HTTP error! status: ${response.status}`
      );
    }

    const disposition = response.headers.get('Content-Disposition') ?? '';
    const filenameMatch = disposition.match(/filename="([^"]+)"/);
    const filename = filenameMatch?.[1] ?? 'richtato-backup.json';
    const blob = await response.blob();
    this.triggerDownload(blob, filename);
  }

  async downloadTransactionsCsv(
    filters: TransactionCsvFilters = {}
  ): Promise<void> {
    const url = new URL(
      `${API_BASE}/auth/backup/export/transactions/`,
      window.location.origin
    );
    if (filters.startDate)
      url.searchParams.set('start_date', filters.startDate);
    if (filters.endDate) url.searchParams.set('end_date', filters.endDate);
    if (filters.accountId)
      url.searchParams.set('account_id', String(filters.accountId));

    const response = await fetchWithAuth(url.toString(), {
      credentials: 'include',
    });
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      throw new Error(
        typeof errorData.error === 'string'
          ? errorData.error
          : `HTTP error! status: ${response.status}`
      );
    }

    const blob = await response.blob();
    this.triggerDownload(blob, 'richtato-transactions.csv');
  }

  async previewImport(file: File): Promise<BackupImportPreview> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.fetchWithCsrf(
      `${API_BASE}/auth/backup/import/preview/`,
      {
        method: 'POST',
        body: formData,
      }
    );
    return this.handleJsonResponse<BackupImportPreview>(response);
  }

  async commitImport(file: File): Promise<BackupImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confirm', 'true');
    const response = await this.fetchWithCsrf(
      `${API_BASE}/auth/backup/import/commit/`,
      {
        method: 'POST',
        body: formData,
      }
    );
    return this.handleJsonResponse<BackupImportResult>(response);
  }
}

export const userBackupApi = new UserBackupApi();
