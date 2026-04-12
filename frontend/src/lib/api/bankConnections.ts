/**
 * Bank Connections API service - Plaid provider
 */
import { BaseApiClient } from './base-client';
import { csrfService } from './csrf';

export type Provider = 'plaid';

export interface BankConnection {
  id: number;
  account: number;
  account_name: string;
  provider: Provider;
  provider_display: string;
  institution_name: string;
  external_account_id: string;
  status: 'active' | 'disconnected' | 'error' | 'pending';
  status_display: string;
  last_sync: string | null;
  sync_frequency: string;
  initial_backfill_complete: boolean;
  oldest_transaction_date: string | null;
  last_sync_error: string | null;
  created_at: string;
}

export interface CreateConnectionInput {
  provider?: Provider;
  access_token: string;
  external_enrollment_id?: string;
  external_account_id?: string;
  institution_name: string;
  account_name?: string;
  account_type?: string;
}

export interface CreateConnectionResponse {
  connections?: BankConnection[];
  id?: number;
  account?: number;
}

export interface SyncResult {
  success: boolean;
  accounts_synced: number;
  transactions_synced: number;
  errors: string[];
  message: string;
}

export interface SyncJobProgress {
  id: number;
  connection: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  status_display: string;
  is_full_sync: boolean;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  transactions_synced: number;
  transactions_skipped: number;
  batches_processed: number;
  errors: string[] | null;
}

class BankConnectionsApiService extends BaseApiClient {
  constructor() {
    super('');
  }

  private async fetchWithCsrf(
    url: string,
    options: RequestInit
  ): Promise<Response> {
    let response = await fetch(url, {
      ...options,
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(url, {
        ...options,
        headers: await csrfService.getHeaders(),
        credentials: 'include',
      });
    }

    return response;
  }

  // ============================================================================
  // Connection Management (Plaid)
  // ============================================================================

  /**
   * Get all bank connections for the authenticated user
   */
  async getConnections(): Promise<BankConnection[]> {
    const response = await fetch(`${this.baseUrl}/sync/connections/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{
      connections: BankConnection[];
    }>(response);
    return data.connections || [];
  }

  /**
   * Create bank connections for all accounts.
   * Backend fetches accounts from the provider and creates connections for each.
   */
  async createConnection(
    input: CreateConnectionInput
  ): Promise<CreateConnectionResponse> {
    const response = await this.fetchWithCsrf(
      `${this.baseUrl}/sync/connections/`,
      {
        method: 'POST',
        body: JSON.stringify(input),
      }
    );

    return this.handleResponse<CreateConnectionResponse>(response);
  }

  /**
   * Disconnect a bank connection
   * @param id - Connection ID
   * @param deleteData - If true, also deletes the account and all its transactions
   */
  async deleteConnection(
    id: number,
    deleteData: boolean = false
  ): Promise<void> {
    const url = deleteData
      ? `${this.baseUrl}/sync/connections/${id}/?delete_data=true`
      : `${this.baseUrl}/sync/connections/${id}/`;

    const response = await this.fetchWithCsrf(url, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to disconnect connection: ${response.status}`);
    }
  }

  /**
   * Trigger sync for a specific connection
   */
  async syncConnection(
    id: number,
    fullSync: boolean = false
  ): Promise<SyncResult> {
    const response = await this.fetchWithCsrf(
      `${this.baseUrl}/sync/connections/${id}/sync/`,
      {
        method: 'POST',
        body: JSON.stringify({ full_sync: fullSync }),
      }
    );

    return this.handleResponse<SyncResult>(response);
  }

  /**
   * Get the progress of the latest sync job for a connection
   */
  async getSyncJobProgress(
    connectionId: number
  ): Promise<SyncJobProgress | null> {
    const response = await fetch(
      `${this.baseUrl}/sync/connections/${connectionId}/progress/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

    const data = await this.handleResponse<{ job: SyncJobProgress | null }>(
      response
    );
    return data.job;
  }

  // ============================================================================
  // Plaid-specific endpoints
  // ============================================================================

  /**
   * Create a Plaid Link token for initializing Plaid Link
   */
  async createPlaidLinkToken(): Promise<string> {
    const response = await this.fetchWithCsrf(
      `${this.baseUrl}/sync/plaid/link-token/`,
      {
        method: 'POST',
        body: JSON.stringify({}),
      }
    );

    const data = await this.handleResponse<{ link_token: string }>(response);
    return data.link_token;
  }

  /**
   * Exchange a Plaid public token for an access token and create connections
   */
  async exchangePlaidToken(
    publicToken: string,
    institutionName: string
  ): Promise<CreateConnectionResponse> {
    const response = await this.fetchWithCsrf(
      `${this.baseUrl}/sync/plaid/exchange-token/`,
      {
        method: 'POST',
        body: JSON.stringify({
          public_token: publicToken,
          institution_name: institutionName,
        }),
      }
    );

    return this.handleResponse<CreateConnectionResponse>(response);
  }

  /**
   * Check if Plaid is configured/available
   */
  isPlaidConfigured(): boolean {
    // Check if Plaid SDK is loaded
    return typeof window !== 'undefined' && !!(window as unknown as { Plaid?: unknown }).Plaid;
  }
}

// Plaid type is declared in usePlaidLink.ts

export const bankConnectionsApiService = new BankConnectionsApiService();
