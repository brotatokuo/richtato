import { csrfService } from '@/lib/api/csrf';
import {
  CreateUserRequest,
  UpdateUserRequest,
  User,
  UserRole,
} from '@/types/user';

/**
 * User API service class for handling user management operations
 * This class abstracts the API calls and provides a clean interface for user CRUD operations
 */
export class UserApiService {
  // TODO: Use baseUrl when implementing actual API calls
  // private readonly baseUrl = '/api/users';

  /**
   * Fetch all users with optional filtering and pagination
   * TODO: Implement actual API call to backend
   */
  async getUsers(_params?: {
    page?: number;
    limit?: number;
    role?: UserRole;
    search?: string;
    organizationId?: string;
  }): Promise<{
    users: User[];
    total: number;
    page: number;
    limit: number;
  }> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}?${new URLSearchParams(params)}`);
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Get a specific user by ID
   * TODO: Implement actual API call to backend
   */
  async getUser(_id: string): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}`);
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Create a new user
   * TODO: Implement actual API call to backend
   */
  async createUser(_userData: CreateUserRequest): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(this.baseUrl, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(userData)
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Update an existing user
   * TODO: Implement actual API call to backend
   */
  async updateUser(_id: string, _userData: UpdateUserRequest): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}`, {
    //   method: 'PUT',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(userData)
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Delete a user
   * TODO: Implement actual API call to backend
   */
  async deleteUser(_id: string): Promise<void> {
    // TODO: Replace with actual API call
    // await fetch(`${this.baseUrl}/${id}`, {
    //   method: 'DELETE'
    // });

    throw new Error('API implementation needed');
  }

  /**
   * Update user role - specialized endpoint for RBAC
   * TODO: Implement actual API call to backend
   */
  async updateUserRole(_id: string, _role: UserRole): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}/role`, {
    //   method: 'PATCH',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ role })
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Get available roles for the current user's organization
   * TODO: Implement actual API call to backend
   */
  async getAvailableRoles(): Promise<UserRole[]> {
    // TODO: Replace with actual API call
    // const response = await fetch('/api/roles');
    // return response.json();

    throw new Error('API implementation needed');
  }
}

export interface CategoryCatalogItem {
  name: string;
  display: string;
  icon: string;
  color: string;
  type: string | null;
  enabled: boolean;
  budget: {
    id: number;
    amount: number;
    start_date: string;
    end_date: string | null;
  } | null;
}

export class CategorySettingsApi {
  private baseUrl = 'http://localhost:8000/api/auth/category-settings';

  private async getHeaders(): Promise<HeadersInit> {
    const headers = await csrfService.getHeaders();
    return headers;
  }

  async getCatalog(): Promise<{ categories: CategoryCatalogItem[] }> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'GET',
      headers: await this.getHeaders(),
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load category settings');
    return res.json();
  }

  async updateSettings(payload: {
    enabled: string[];
    disabled: string[];
    budgets?: Record<
      string,
      { amount: number | null; start_date?: string; end_date?: string | null }
    >;
  }): Promise<{ success: boolean }> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'PUT',
      headers: await this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update category settings');
    return res.json();
  }
}

// Export singleton instance
export const userApi = new UserApiService();
export const categorySettingsApi = new CategorySettingsApi();

// Cards / Accounts helpers
export interface CardAccountItem {
  id: number;
  name: string;
  bank: string;
}

class CardsApiService {
  private baseUrl = 'http://localhost:8000/api/auth/card-accounts';

  async list(): Promise<CardAccountItem[]> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load card accounts');
    const data = await res.json();
    return data as CardAccountItem[];
  }
}

export const cardsApi = new CardsApiService();

// Preferences API
export type ThemePref = 'light' | 'dark' | 'system';
export interface UserPreferencesPayload {
  theme?: ThemePref;
  currency?: string;
  date_format?: string;
}

class PreferencesApiService {
  private baseUrl = 'http://localhost:8000/api/auth/preferences';

  async get(): Promise<UserPreferencesPayload> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'GET',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load preferences');
    return res.json();
  }

  async update(
    payload: UserPreferencesPayload
  ): Promise<UserPreferencesPayload> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'PUT',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update preferences');
    return res.json();
  }
}

export const preferencesApi = new PreferencesApiService();
