/**
 * Teller API service for bank connections
 */
import { csrfService } from './csrf';

export interface TellerConnection {
  id: number;
  teller_account_id: string;
  enrollment_id: string;
  institution_name: string;
  account_name: string;
  account_type: string;
  status: 'active' | 'disconnected' | 'error';
  last_sync: string | null;
  last_sync_error: string;
  created_at: string;
}

export interface CreateTellerConnectionInput {
  access_token: string;
  enrollment_id?: string;
  teller_account_id: string;
  institution_name: string;
  account_name: string;
  account_type?: string;
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
      rows: TellerConnection[];
    }>(response);
    return data.rows || [];
  }

  /**
   * Create a new Teller connection
   */
  async saveTellerConnection(
    input: CreateTellerConnectionInput
  ): Promise<TellerConnection> {
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

    return this.handleResponse<TellerConnection>(response);
  }

  /**
   * Disconnect a Teller connection
   */
  async deleteTellerConnection(id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/teller/connections/${id}/`,
      {
        method: 'DELETE',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to disconnect Teller connection: ${response.status}`);
    }
  }

  /**
   * Trigger sync for a specific Teller connection
   */
  async syncTellerConnection(
    id: number,
    days: number = 30
  ): Promise<TellerSyncResult> {
    let response = await fetch(`${this.baseUrl}/teller/sync/${id}/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ days }),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for Teller sync, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/teller/sync/${id}/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({ days }),
      });
    }

    return this.handleResponse<TellerSyncResult>(response);
  }
}

export const tellerApiService = new TellerApiService();
