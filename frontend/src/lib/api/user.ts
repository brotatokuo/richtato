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

export type CategoryType =
  | 'income'
  | 'expense'
  | 'transfer'
  | 'investment'
  | 'other';

export interface CategoryKeyword {
  id: number;
  keyword: string;
  match_count: number;
  created_at: string;
}

export interface CategoryCatalogItem {
  id: number;
  name: string;
  display: string;
  icon: string;
  color: string;
  type: string | null;
  enabled: boolean;
  keywords?: CategoryKeyword[];
  // Deprecated fields - kept for backward compatibility but not returned by API
  is_income?: boolean;
  is_expense?: boolean;
  budget: {
    id: number;
    amount: number;
    start_date: string;
    end_date: string | null;
  } | null;
}

export interface CategorySettingsPayload {
  enabled: string[];
  disabled: string[];
  budgets?: Record<
    string,
    { amount: number | null; start_date?: string; end_date?: string | null }
  >;
  category_types?: Record<string, CategoryType>;
}

export class CategorySettingsApi {
  private baseUrl = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/category-settings`;
  private keywordBase = `${
    import.meta.env.VITE_API_BASE_URL || '/api/v1'
  }/transactions/categories`;

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

  async updateSettings(
    payload: CategorySettingsPayload
  ): Promise<{ success: boolean }> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'PUT',
      headers: await this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update category settings');
    return res.json();
  }

  async getCategoryKeywords(categoryId: number): Promise<{
    keywords: CategoryKeyword[];
  }> {
    const res = await fetch(`${this.keywordBase}/${categoryId}/keywords/`, {
      method: 'GET',
      headers: await this.getHeaders(),
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load keywords');
    return res.json();
  }

  async addCategoryKeyword(
    categoryId: number,
    keyword: string
  ): Promise<CategoryKeyword> {
    await csrfService.refreshToken();
    const res = await fetch(`${this.keywordBase}/${categoryId}/keywords/`, {
      method: 'POST',
      headers: await this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ keyword }),
    });
    if (!res.ok) throw new Error('Failed to add keyword');
    return res.json();
  }

  async deleteCategoryKeyword(
    categoryId: number,
    keywordId: number
  ): Promise<void> {
    await csrfService.refreshToken();
    const res = await fetch(
      `${this.keywordBase}/${categoryId}/keywords/${keywordId}/`,
      {
        method: 'DELETE',
        headers: await this.getHeaders(),
        credentials: 'include',
      }
    );
    if (!res.ok) throw new Error('Failed to delete keyword');
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
  imageKey?: string | null;
}

// API response format (snake_case from backend)
interface CardAccountApiResponse {
  id: number;
  name: string;
  entity: string;
  image_key?: string | null;
}

// Transform API response to frontend format
function transformCardAccount(
  apiItem: CardAccountApiResponse
): CardAccountItem {
  return {
    id: apiItem.id,
    name: apiItem.name,
    bank: apiItem.entity,
    imageKey: apiItem.image_key ?? null,
  };
}

class CardsApiService {
  private baseUrl = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/card-accounts`;

  async list(): Promise<CardAccountItem[]> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load card accounts');
    const data = await res.json();

    // Extract array from response
    let rawItems: CardAccountApiResponse[] = [];
    if (Array.isArray(data)) {
      rawItems = data;
    } else if (data && typeof data === 'object') {
      if (Array.isArray(data.rows)) rawItems = data.rows;
      else if (Array.isArray(data.cards)) rawItems = data.cards;
      else if (Array.isArray(data.results)) rawItems = data.results;
      else if (Array.isArray(data.data)) rawItems = data.data;
      else {
        console.warn('Unexpected card accounts API response format:', data);
        return [];
      }
    }

    // Transform snake_case to camelCase
    return rawItems.map(transformCardAccount);
  }

  async create(payload: {
    name: string;
    bank: string;
  }): Promise<CardAccountItem> {
    const res = await fetch(`${this.baseUrl}/`, {
      method: 'POST',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create card account');
    return res.json();
  }

  async update(
    id: number,
    payload: Partial<{ name: string; bank: string; image_key: string | null }>
  ): Promise<CardAccountItem> {
    const res = await fetch(`${this.baseUrl}/${id}/`, {
      method: 'PATCH',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update card account');
    return res.json();
  }

  async remove(id: number): Promise<void> {
    const res = await fetch(`${this.baseUrl}/${id}/`, {
      method: 'DELETE',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete card account');
  }

  async getFieldChoices(): Promise<{
    bank: Array<{ value: string; label: string }>;
  }> {
    const res = await fetch(`${this.baseUrl}/field-choices/`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load field choices');
    return res.json();
  }
}

export const cardsApi = new CardsApiService();

// Preferences API
export type ThemePref = 'light' | 'dark' | 'system';
export interface UserPreferencesPayload {
  theme?: ThemePref;
  currency?: string;
  date_format?: string;
  timezone?: string;
  notifications_enabled?: boolean;
}

export interface FieldChoice {
  value: string;
  label: string;
}

export interface PreferenceFieldChoices {
  theme: FieldChoice[];
  date_format: FieldChoice[];
  currency: FieldChoice[];
  timezone: FieldChoice[];
}

class PreferencesApiService {
  private baseUrl = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/preferences`;

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
    // Always refresh CSRF token before write operations to avoid 403 errors
    await csrfService.refreshToken();
    const csrfHeaders = await csrfService.getHeaders();

    const res = await fetch(`${this.baseUrl}/`, {
      method: 'PUT',
      credentials: 'include',
      headers: csrfHeaders,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Failed to update preferences: ${res.status}`);
    }
    return res.json();
  }

  async getFieldChoices(): Promise<PreferenceFieldChoices> {
    const res = await fetch(`${this.baseUrl}/field-choices/`, {
      method: 'GET',
      credentials: 'include',
      headers: await csrfService.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load field choices');
    return res.json();
  }
}

export const preferencesApi = new PreferencesApiService();
