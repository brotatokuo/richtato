/**
 * Bank Sync API service.
 *
 * Talks to the `/api/v1/bank-sync/` endpoints that power the cookie-only
 * Playwright agent flow. The agent never sees passwords; the user signs in
 * to their bank in a headed Chromium window driven by the agent and only
 * the resulting browser cookies are captured and encrypted server-side.
 */
import { BaseApiClient } from './base-client';
import { csrfService } from './csrf';
import { fetchWithAuth } from './fetchClient';

export type BankSyncCadence = 'manual' | 'daily' | 'weekly' | 'monthly';

export type BankSyncStatus =
  | 'pending_login'
  | 'active'
  | 'needs_reauth'
  | 'disabled'
  | 'error';

export type BankSyncFlow = 'deposit' | 'credit_card';

export type BankSyncTaskKind =
  | 'interactive_login'
  | 'scheduled_download'
  | 'manual_download';

export type BankSyncRunStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'partial';

export interface SyncedAccount {
  id: number;
  bank_login: number;
  financial_account: number;
  financial_account_name: string;
  financial_account_type: string;
  flow: BankSyncFlow;
  external_account_token: string;
  detected_account_name: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankLogin {
  id: number;
  institution: number;
  institution_name: string;
  institution_slug: string;
  nickname: string;
  status: BankSyncStatus;
  status_display: string;
  cadence: BankSyncCadence;
  cadence_display: string;
  preferred_run_hour_local: number;
  cookies_captured_at: string | null;
  cookies_expected_to_expire_at: string | null;
  last_run_at: string | null;
  last_success_at: string | null;
  next_run_at: string | null;
  consecutive_failures: number;
  last_failure_reason: string;
  synced_accounts: SyncedAccount[];
  created_at: string;
  updated_at: string;
}

export interface BankLoginCreate {
  institution: number;
  nickname?: string;
  cadence?: BankSyncCadence;
  preferred_run_hour_local?: number;
}

export interface BankLoginUpdate {
  cadence?: BankSyncCadence;
  preferred_run_hour_local?: number;
  nickname?: string;
  enabled?: boolean;
}

export interface SupportedInstitution {
  id: number | null;
  slug: string;
  name: string;
  supports_deposit: boolean;
  supports_credit_card: boolean;
}

export interface BindableAccount {
  id: number;
  name: string;
  account_type: string;
  account_type_display: string;
  account_number_last4: string;
  institution_slug: string;
  institution_name: string;
  flow: BankSyncFlow;
  matches_institution: boolean;
  already_bound: boolean;
}

export interface SyncRun {
  id: number;
  bank_login: number;
  task_kind: BankSyncTaskKind;
  task_kind_display: string;
  status: BankSyncRunStatus;
  status_display: string;
  triggered_by: string;
  queued_at: string;
  leased_at: string | null;
  finished_at: string | null;
  failure_kind: string;
  failure_reason: string;
  accounts_attempted: number;
  accounts_succeeded: number;
  statements_imported: number;
  duration_seconds: number | null;
}

export interface BulkBindRow {
  bank_login: number;
  financial_account: number;
  flow: BankSyncFlow;
  external_account_token?: string;
  activity_url?: string;
  detected_account_name?: string;
}

class BankSyncApiService extends BaseApiClient {
  constructor() {
    super('/bank-sync');
  }

  private async fetchMutating(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    let response = await fetchWithAuth(url, {
      ...options,
      headers: {
        ...(await csrfService.getHeaders()),
        ...(options.headers || {}),
      },
      credentials: 'include',
    });

    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetchWithAuth(url, {
        ...options,
        headers: {
          ...(await csrfService.getHeaders()),
          ...(options.headers || {}),
        },
        credentials: 'include',
      });
    }

    return response;
  }

  async listLogins(): Promise<BankLogin[]> {
    const response = await fetchWithAuth(`${this.baseUrl}/logins/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{ logins: BankLogin[] }>(response);
    return data.logins || [];
  }

  async createLogin(payload: BankLoginCreate): Promise<BankLogin> {
    const response = await this.fetchMutating(`${this.baseUrl}/logins/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return this.handleResponse<BankLogin>(response);
  }

  async getLogin(id: number): Promise<BankLogin> {
    const response = await fetchWithAuth(`${this.baseUrl}/logins/${id}/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<BankLogin>(response);
  }

  async updateLogin(id: number, patch: BankLoginUpdate): Promise<BankLogin> {
    const response = await this.fetchMutating(`${this.baseUrl}/logins/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
    return this.handleResponse<BankLogin>(response);
  }

  async deleteLogin(id: number): Promise<void> {
    const response = await this.fetchMutating(`${this.baseUrl}/logins/${id}/`, {
      method: 'DELETE',
    });
    if (!response.ok && response.status !== 204) {
      throw new Error(`Failed to delete login: ${response.status}`);
    }
  }

  async disableLogin(id: number): Promise<BankLogin> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/logins/${id}/disable/`,
      { method: 'POST' }
    );
    return this.handleResponse<BankLogin>(response);
  }

  async beginLogin(id: number): Promise<{ run_id: number; queued_at: string }> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/logins/${id}/begin-login/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async syncNow(id: number): Promise<{ run_id: number; queued_at: string }> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/logins/${id}/sync-now/`,
      { method: 'POST' }
    );
    return this.handleResponse(response);
  }

  async listRuns(loginId: number): Promise<SyncRun[]> {
    const response = await fetchWithAuth(
      `${this.baseUrl}/logins/${loginId}/runs/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    const data = await this.handleResponse<{ runs: SyncRun[] }>(response);
    return data.runs || [];
  }

  async listSyncedAccounts(): Promise<SyncedAccount[]> {
    const response = await fetchWithAuth(`${this.baseUrl}/synced-accounts/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{ accounts: SyncedAccount[] }>(
      response
    );
    return data.accounts || [];
  }

  async updateSyncedAccount(
    id: number,
    patch: { enabled?: boolean; flow?: BankSyncFlow }
  ): Promise<SyncedAccount> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/synced-accounts/${id}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(patch),
      }
    );
    return this.handleResponse<SyncedAccount>(response);
  }

  async deleteSyncedAccount(id: number): Promise<void> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/synced-accounts/${id}/`,
      { method: 'DELETE' }
    );
    if (!response.ok && response.status !== 204) {
      throw new Error(`Failed to delete synced account: ${response.status}`);
    }
  }

  async bulkBind(rows: BulkBindRow[]): Promise<SyncedAccount[]> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/synced-accounts/bulk-bind/`,
      {
        method: 'POST',
        body: JSON.stringify({ accounts: rows }),
      }
    );
    const data = await this.handleResponse<{ accounts: SyncedAccount[] }>(
      response
    );
    return data.accounts || [];
  }

  async listSupportedInstitutions(): Promise<SupportedInstitution[]> {
    const response = await fetchWithAuth(
      `${this.baseUrl}/supported-institutions/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    const data = await this.handleResponse<{
      institutions: SupportedInstitution[];
    }>(response);
    return data.institutions || [];
  }

  async listBindableAccounts(
    institutionSlug?: string
  ): Promise<BindableAccount[]> {
    const query = institutionSlug
      ? `?institution_slug=${encodeURIComponent(institutionSlug)}`
      : '';
    const response = await fetchWithAuth(
      `${this.baseUrl}/bindable-accounts/${query}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    const data = await this.handleResponse<{ accounts: BindableAccount[] }>(
      response
    );
    return data.accounts || [];
  }
}

export const bankSyncApi = new BankSyncApiService();
