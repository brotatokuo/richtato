/**
 * Teller API service for bank connections
 */
import { csrfService } from './csrf';

export interface TellerConnection {
  id: number;
  account: number;
  account_name: string;
  provider: string;
  provider_display: string;
  institution_name: string;
  external_account_id: string;
  status: 'active' | 'disconnected' | 'error';
  status_display: string;
  last_sync: string | null;
  sync_frequency: string;
  initial_backfill_complete: boolean;
  oldest_transaction_date: string | null;
  last_sync_error: string | null;
  created_at: string;
}

export interface CreateTellerConnectionInput {
  access_token: string;
  external_enrollment_id?: string;
  external_account_id?: string;
  institution_name: string;
  account_name?: string;
  account_type?: string;
}

export interface CreateTellerConnectionResponse {
  connections?: TellerConnection[];
  // Single connection response (backwards compatibility)
  id?: number;
  account?: number;
}

export interface TellerSyncResult {
  success: boolean;
  accounts_synced: number;
  transactions_synced: number;
  errors: string[];
  message: string;
}

class TellerApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  }

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    };
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

  /**
   * Get all Teller connections for the authenticated user
   */
  async getTellerConnections(): Promise<TellerConnection[]> {
    const response = await fetch(`${this.baseUrl}/teller/connections/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{
      connections: TellerConnection[];
    }>(response);
    return data.connections || [];
  }

  /**
   * Create Teller connections for all accounts in an enrollment.
   * Backend fetches accounts from Teller and creates connections for each.
   */
  async saveTellerConnection(
    input: CreateTellerConnectionInput
  ): Promise<CreateTellerConnectionResponse> {
    let response = await fetch(`${this.baseUrl}/teller/connections/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for Teller connection, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/teller/connections/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      });
    }

    return this.handleResponse<CreateTellerConnectionResponse>(response);
  }

  /**
   * Disconnect a Teller connection
   */
  async deleteTellerConnection(id: number): Promise<void> {
    let response = await fetch(
      `${this.baseUrl}/teller/connections/${id}/`,
      {
        method: 'DELETE',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
      }
    );

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for Teller delete, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(
        `${this.baseUrl}/teller/connections/${id}/`,
        {
          method: 'DELETE',
          headers: await csrfService.getHeaders(),
          credentials: 'include',
        }
      );
    }

    if (!response.ok) {
      throw new Error(`Failed to disconnect Teller connection: ${response.status}`);
    }
  }

  /**
   * Trigger sync for a specific Teller connection
   */
  async syncTellerConnection(
    id: number,
    fullSync: boolean = false
  ): Promise<TellerSyncResult> {
    let response = await fetch(`${this.baseUrl}/teller/connections/${id}/sync/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ full_sync: fullSync }),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for Teller sync, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/teller/connections/${id}/sync/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({ full_sync: fullSync }),
      });
    }

    return this.handleResponse<TellerSyncResult>(response);
  }
}

export const tellerApiService = new TellerApiService();
