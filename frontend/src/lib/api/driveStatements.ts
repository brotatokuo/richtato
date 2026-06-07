import { csrfService } from './csrf';
import { fetchWithAuth } from './fetchClient';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface DriveAccountFolder {
  account: number;
  account_name: string;
  folder_id: string;
  folder_name: string;
  storage_uri: string;
}

export interface DriveStatus {
  configured: boolean;
  connected: boolean;
  active: boolean;
  google_account_email?: string;
  root_folder_id?: string;
  root_folder_name?: string;
  connected_at?: string | null;
  activated_at?: string | null;
  last_error?: string;
  missing_folder_count?: number;
  account_folders: DriveAccountFolder[];
}

export interface PickerTokenResponse {
  access_token: string;
  client_id: string;
  developer_key: string;
  app_id: string;
}

export interface DriveAdoptPreview {
  root_folder_id: string;
  root_folder_name: string;
  adopted: Array<{
    account_id: number;
    account_name: string;
    folder_id: string;
    folder_name: string;
    statement_file_count: number;
  }>;
  would_create: Array<{
    account_id: number;
    account_name: string;
    expected_folder_name: string;
  }>;
  unmatched: Array<{
    folder_id: string;
    folder_name: string;
    parsed_account_id: number | null;
  }>;
  statement_file_counts: Record<string, number>;
  errors: Array<{ message: string }>;
}

export interface DriveScanSummary {
  accounts_scanned: number;
  files_seen: number;
  files_imported: number;
  files_skipped: number;
  files_failed: number;
  files_removed: number;
}

class DriveStatementsApi {
  async getStatus(): Promise<DriveStatus> {
    const response = await fetchWithAuth(`${API_BASE}/accounts/drive/status/`, {
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  async startOAuth(): Promise<{ auth_url: string }> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/oauth/start/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async getPickerToken(): Promise<PickerTokenResponse> {
    const response = await fetchWithAuth(
      `${API_BASE}/accounts/drive/picker-token/`,
      {
        credentials: 'include',
      }
    );
    return this.handleResponse(response);
  }

  async adoptPreview(folderId: string): Promise<DriveAdoptPreview> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/adopt-preview/`,
      {
        method: 'POST',
        body: JSON.stringify({ folder_id: folderId }),
      }
    );
    return this.handleResponse(response);
  }

  async activate(input: {
    folderId: string;
    folderName: string;
    adoptExisting?: boolean;
  }): Promise<{
    status: DriveStatus;
    account_folders_created: number;
    account_folders_adopted: number;
    unmatched_drive_folders: DriveAdoptPreview['unmatched'];
    scan_summary: DriveScanSummary | null;
    errors: string[];
  }> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/activate/`,
      {
        method: 'POST',
        body: JSON.stringify({
          folder_id: input.folderId,
          folder_name: input.folderName,
          adopt_existing: Boolean(input.adoptExisting),
        }),
      }
    );
    return this.handleResponse(response);
  }

  async deactivate(): Promise<{
    status: DriveStatus;
    account_folders_removed: number;
    errors: string[];
  }> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/deactivate/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async disconnect(): Promise<DriveStatus> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/disconnect/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async syncMissingFolders(): Promise<{
    status: DriveStatus;
    account_folders_created: number;
    errors: string[];
  }> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/drive/sync-folders/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
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

export const driveStatementsApi = new DriveStatementsApi();
