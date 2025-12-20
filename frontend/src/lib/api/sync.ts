/**
 * Sync API service for bank connection sync status.
 *
 * This service is used to:
 * 1. Poll for sync status (to show syncing indicator/badge)
 * 2. Clear new transaction count when user views transactions
 *
 * Sync triggering is handled automatically by the backend middleware
 * when the user makes any authenticated request with stale connections.
 */

import { csrfService } from './csrf';

export interface SyncStatus {
  is_syncing: boolean;
  new_transaction_count: number;
  last_sync: string | null;
}

export interface SyncTriggerResponse {
  status: 'sync_started' | 'no_connections';
  message: string;
}

class SyncService {
  private baseUrl = '/api/v1/sync';

  /**
   * Get the current sync status for the authenticated user.
   */
  async getStatus(): Promise<SyncStatus> {
    const response = await fetch(`${this.baseUrl}/status/`, {
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to get sync status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Clear the new transaction count (call after user views transactions).
   */
  async clearNewCount(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/status/`, {
      method: 'DELETE',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to clear new count: ${response.status}`);
    }
  }

  /**
   * Trigger sync for all user connections (runs in background).
   */
  async triggerSyncAll(): Promise<SyncTriggerResponse> {
    // Force refresh CSRF token before POST to ensure we have a valid token
    await csrfService.refreshToken();

    const headers = await csrfService.getHeaders();
    console.log('Sync POST headers:', headers);

    const response = await fetch(`${this.baseUrl}/status/`, {
      method: 'POST',
      credentials: 'include',
      headers,
    });

    console.log('Sync POST response:', response.status);

    if (!response.ok) {
      const text = await response.text();
      console.error('Sync POST error:', text);
      throw new Error(`Failed to trigger sync: ${response.status}`);
    }

    return response.json();
  }
}

export const syncService = new SyncService();
