/**
 * Bank Automation API service.
 *
 * Talks to the new `/api/v1/bank-automation/` endpoints introduced for the
 * Chrome-extension-driven download flow. Coexists with the existing
 * `bankConnections.ts` service which targets the Plaid-based path.
 */
import { BaseApiClient } from './base-client';
import { csrfService } from './csrf';
import { fetchWithAuth } from './fetchClient';

export type BankAutomationCadence =
  | 'manual'
  | 'daily'
  | 'weekly'
  | 'biweekly'
  | 'monthly';

export type BankAutomationStatus =
  | 'active'
  | 'reauth_required'
  | 'disabled'
  | 'error';

export interface BankAutomationAccountLink {
  id: number;
  /** Null when the user captured a session but hasn't bound it to a Richtato account yet. */
  financial_account: number | null;
  financial_account_name: string;
  financial_account_type: string;
  flow: 'deposit' | 'credit_card';
  external_account_token: string;
  detected_account_name: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankAutomationConnection {
  id: number;
  institution: number;
  institution_name: string;
  institution_slug: string;
  login_id: string;
  nickname: string;
  status: BankAutomationStatus;
  status_display: string;
  cadence: BankAutomationCadence;
  cadence_display: string;
  preferred_run_hour_local: number;
  last_run_at: string | null;
  last_success_at: string | null;
  next_run_at: string | null;
  consecutive_failures: number;
  last_failure_reason: string;
  next_reauth_estimated_at: string | null;
  account_links: BankAutomationAccountLink[];
  created_at: string;
  updated_at: string;
}

export interface BankAutomationConnectionUpdate {
  cadence?: BankAutomationCadence;
  preferred_run_hour_local?: number;
  nickname?: string;
  enabled?: boolean;
}

export interface SupportedInstitution {
  slug: string;
  name: string;
  supports_deposit: boolean;
  supports_credit_card: boolean;
}

export interface BankAutomationRun {
  id: number;
  connection: number;
  started_at: string;
  finished_at: string | null;
  status: 'running' | 'completed' | 'failed' | 'partial';
  status_display: string;
  failure_kind: string;
  failure_reason: string;
  accounts_attempted: number;
  accounts_succeeded: number;
  statements_imported: number;
  triggered_by: string;
  duration_seconds: number | null;
}

class BankAutomationApiService extends BaseApiClient {
  constructor() {
    super('/bank-automation');
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

  async listConnections(): Promise<BankAutomationConnection[]> {
    const response = await fetchWithAuth(`${this.baseUrl}/connections/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{
      connections: BankAutomationConnection[];
    }>(response);
    return data.connections || [];
  }

  async getConnection(id: number): Promise<BankAutomationConnection> {
    const response = await fetchWithAuth(`${this.baseUrl}/connections/${id}/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<BankAutomationConnection>(response);
  }

  async updateConnection(
    id: number,
    patch: BankAutomationConnectionUpdate
  ): Promise<BankAutomationConnection> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/connections/${id}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(patch),
      }
    );
    return this.handleResponse<BankAutomationConnection>(response);
  }

  async deleteConnection(id: number): Promise<void> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/connections/${id}/`,
      { method: 'DELETE' }
    );
    if (!response.ok && response.status !== 204) {
      throw new Error(`Failed to delete connection: ${response.status}`);
    }
  }

  async disableConnection(id: number): Promise<BankAutomationConnection> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/connections/${id}/disable/`,
      { method: 'POST' }
    );
    return this.handleResponse<BankAutomationConnection>(response);
  }

  async runConnection(id: number): Promise<{ queued_at: string }> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/connections/${id}/run/`,
      { method: 'POST' }
    );
    return this.handleResponse<{ queued_at: string }>(response);
  }

  async listRuns(connectionId: number): Promise<BankAutomationRun[]> {
    const response = await fetchWithAuth(
      `${this.baseUrl}/connections/${connectionId}/runs/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    const data = await this.handleResponse<{ runs: BankAutomationRun[] }>(
      response
    );
    return data.runs || [];
  }

  async updateAccountLink(
    linkId: number,
    patch: { enabled?: boolean; financial_account_id?: number }
  ): Promise<{ id: number; enabled: boolean }> {
    const response = await this.fetchMutating(
      `${this.baseUrl}/account-links/${linkId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(patch),
      }
    );
    return this.handleResponse(response);
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
}

export const bankAutomationApi = new BankAutomationApiService();
