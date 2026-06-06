import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface InAppNotification {
  id: number;
  source: string;
  source_key: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  title: string;
  body: string;
  action_url: string;
  metadata: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: InAppNotification[];
  unread_count: number;
}

class NotificationsApi {
  async list(options?: { unread?: boolean; limit?: number }) {
    const params = new URLSearchParams();
    if (options?.unread) params.set('unread', '1');
    if (options?.limit) params.set('limit', String(options.limit));
    const query = params.toString();
    const response = await fetch(
      `${API_BASE}/core/notifications/${query ? `?${query}` : ''}`,
      { credentials: 'include' }
    );
    if (!response.ok) throw new Error('Failed to load notifications');
    return response.json() as Promise<NotificationsResponse>;
  }

  async markRead(id: number) {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/core/notifications/${id}/`,
      {
        method: 'PATCH',
        body: JSON.stringify({ read: true }),
      }
    );
    if (!response.ok) throw new Error('Failed to update notification');
    return response.json() as Promise<InAppNotification>;
  }

  async markAllRead() {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/core/notifications/mark-all-read/`,
      { method: 'POST' }
    );
    if (!response.ok) throw new Error('Failed to mark notifications read');
    return response.json() as Promise<{ updated: number }>;
  }
}

export const notificationsApi = new NotificationsApi();
