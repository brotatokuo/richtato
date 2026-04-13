/**
 * Household API service for couples/family finance tracking.
 */
import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface HouseholdMember {
  user_id: number;
  username: string;
  joined_at: string;
}

export interface Household {
  id: number;
  name: string;
  members: HouseholdMember[];
  created_at: string;
}

export interface InviteCodeResponse {
  invite_code: string;
  expires_at: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error || `HTTP error! status: ${response.status}`
    );
  }
  return response.json();
}

class HouseholdApiService {
  async getHousehold(): Promise<Household> {
    const response = await fetch(`${API_BASE}/household/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    return handleResponse<Household>(response);
  }

  async createHousehold(name: string): Promise<Household> {
    const response = await csrfService.fetchWithCsrf(`${API_BASE}/household/`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    return handleResponse<Household>(response);
  }

  async generateInviteCode(): Promise<InviteCodeResponse> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/household/invite/`,
      { method: 'POST' }
    );
    return handleResponse<InviteCodeResponse>(response);
  }

  async joinHousehold(code: string): Promise<Household> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/household/join/`,
      {
        method: 'POST',
        body: JSON.stringify({ code }),
      }
    );
    return handleResponse<Household>(response);
  }

  async leaveHousehold(): Promise<void> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/household/leave/`,
      { method: 'POST' }
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to leave household');
    }
  }

  async getMembers(): Promise<{ members: HouseholdMember[] }> {
    const response = await fetch(`${API_BASE}/household/members/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    return handleResponse<{ members: HouseholdMember[] }>(response);
  }
}

export const householdApi = new HouseholdApiService();
