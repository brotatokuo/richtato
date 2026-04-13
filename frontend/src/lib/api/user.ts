import { csrfService } from '@/lib/api/csrf';

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

export type ExpensePriority = 'essential' | 'non_essential' | null;

export interface CategoryCatalogItem {
  id: number;
  name: string;
  display: string;
  icon: string;
  color: string;
  type: string | null;
  expense_priority?: ExpensePriority;
  is_essential?: boolean;
  enabled: boolean;
  keywords?: CategoryKeyword[];
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
    const res = await csrfService.fetchWithCsrf(
      `${this.keywordBase}/${categoryId}/keywords/`,
      { method: 'POST', body: JSON.stringify({ keyword }) }
    );
    if (!res.ok) throw new Error('Failed to add keyword');
    return res.json();
  }

  async deleteCategoryKeyword(
    categoryId: number,
    keywordId: number
  ): Promise<void> {
    const res = await csrfService.fetchWithCsrf(
      `${this.keywordBase}/${categoryId}/keywords/${keywordId}/`,
      { method: 'DELETE' }
    );
    if (!res.ok) throw new Error('Failed to delete keyword');
  }

  async updateCategoryExpensePriority(
    categoryId: number,
    expensePriority: ExpensePriority
  ): Promise<CategoryCatalogItem> {
    const res = await csrfService.fetchWithCsrf(
      `${this.keywordBase}/${categoryId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify({ expense_priority: expensePriority }),
      }
    );
    if (!res.ok) throw new Error('Failed to update category');
    return res.json();
  }

  async createCategory(data: {
    name: string;
    type: 'income' | 'expense' | 'transfer' | 'investment' | 'other';
    icon?: string;
    color?: string;
  }): Promise<CategoryCatalogItem> {
    const res = await csrfService.fetchWithCsrf(`${this.keywordBase}/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create category');
    return res.json();
  }

  async deleteCategory(categoryId: number): Promise<void> {
    const res = await csrfService.fetchWithCsrf(
      `${this.keywordBase}/${categoryId}/`,
      { method: 'DELETE' }
    );
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || 'Failed to delete category');
    }
  }
}

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
