/**
 * Transactions API service for fetching income and expense data
 */
import { csrfService } from './csrf';

export interface Transaction {
  id: number;
  description: string;
  date: string;
  amount: number;
  Account?: string;
  Category?: string;
}

// Creation payloads differ from the read model. Backend expects numeric IDs.
export interface CreateIncomeTransactionInput {
  description: string;
  date: string; // YYYY-MM-DD
  amount: number;
  Account: number; // account primary key
}

export interface CreateExpenseTransactionInput {
  description: string;
  date: string; // YYYY-MM-DD
  amount: number;
  account_name: number; // account primary key
  category?: number; // category primary key
}

export interface Account {
  id: number;
  name: string;
  type: string;
  balance?: number;
  entity?: string;
  date?: string;
}

export interface Category {
  id: number;
  name: string;
  type: string;
}

export interface FieldChoiceItem {
  value: number;
  label: string;
}

export interface ExpenseFieldChoicesResponse {
  account: FieldChoiceItem[];
  category: FieldChoiceItem[];
}

export interface Budget {
  id: number;
  category: string;
  amount: number;
  start_date: string;
  end_date: string;
}

class TransactionsApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
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
   * Get income transactions
   */
  async getIncomeTransactions(input?: {
    limit?: number;
    startDate?: string; // YYYY-MM-DD
    endDate?: string; // YYYY-MM-DD
  }): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/income/`, window.location.origin);
    if (input?.limit) {
      url.searchParams.append('limit', input.limit.toString());
    }
    if (input?.startDate)
      url.searchParams.append('start_date', input.startDate);
    if (input?.endDate) url.searchParams.append('end_date', input.endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ rows: Transaction[] }>(response);
    return data.rows || [];
  }

  /**
   * Get expense transactions
   */
  async getExpenseTransactions(input?: {
    limit?: number;
    startDate?: string; // YYYY-MM-DD
    endDate?: string; // YYYY-MM-DD
  }): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/expense/`, window.location.origin);
    if (input?.limit) {
      url.searchParams.append('limit', input.limit.toString());
    }
    if (input?.startDate)
      url.searchParams.append('start_date', input.startDate);
    if (input?.endDate) url.searchParams.append('end_date', input.endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ rows: Transaction[] }>(response);
    return data.rows || [];
  }

  /**
   * Get all accounts
   */
  async getAccounts(): Promise<Account[]> {
    const response = await fetch(`${this.baseUrl}/accounts/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ rows: Account[] }>(response);
    return data.rows || [];
  }

  /**
   * Get transactions (balance history) for an account
   */
  async getAccountTransactions(
    accountId: number,
    input?: {
      page?: number;
      pageSize?: number;
    }
  ): Promise<{
    columns: Array<{ field: string; title: string }>;
    rows: Array<{ id: number; date: string; amount: string }>;
    page: number;
    page_size: number;
    total: number;
  }> {
    const url = new URL(
      `${this.baseUrl}/accounts/${accountId}/transactions/`,
      window.location.origin
    );
    if (input?.page) url.searchParams.append('page', String(input.page));
    if (input?.pageSize)
      url.searchParams.append('page_size', String(input.pageSize));
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  /**
   * Create a balance update (account transaction)
   */
  async createAccountTransaction(input: {
    account: number;
    amount: number;
    date: string; // YYYY-MM-DD
  }): Promise<any> {
    const response = await fetch(`${this.baseUrl}/accounts/details/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });
    return this.handleResponse(response);
  }

  async updateAccountTransaction(
    accountId: number,
    input: {
      id: number;
      amount?: number;
      date?: string;
    }
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/accounts/${accountId}/transactions/`,
      {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      }
    );
    return this.handleResponse(response);
  }

  async deleteAccountTransaction(accountId: number, id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/accounts/${accountId}/transactions/`,
      {
        method: 'DELETE',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({ id }),
      }
    );
    if (!response.ok) throw new Error('Failed to delete transaction');
  }

  /**
   * Create an account
   */
  async createAccount(input: {
    name: string;
    type: string;
    asset_entity_name?: string;
  }): Promise<Account> {
    const response = await fetch(`${this.baseUrl}/accounts/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });

    return this.handleResponse<Account>(response);
  }

  /**
   * Update an account
   */
  async updateAccount(
    id: number,
    input: Partial<{ name: string; type: string; asset_entity_name: string }>
  ): Promise<Account> {
    const response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
      method: 'PATCH',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });

    return this.handleResponse<Account>(response);
  }

  /**
   * Delete an account
   */
  async deleteAccount(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
      method: 'DELETE',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete account: ${response.status}`);
    }
  }

  /**
   * Get all categories
   */
  async getCategories(): Promise<Category[]> {
    const response = await fetch(`${this.baseUrl}/auth/categories/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ results: Category[] }>(response);
    return data.results || [];
  }

  /**
   * Get expense field choices (CardAccounts and Categories)
   */
  async getExpenseFieldChoices(): Promise<{
    accounts: Account[];
    categories: Category[];
  }> {
    const response = await fetch(`${this.baseUrl}/expense/field-choices/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data =
      await this.handleResponse<ExpenseFieldChoicesResponse>(response);
    const accounts: Account[] = (data.account || []).map(item => ({
      id: item.value,
      name: item.label,
      type: 'card',
    }));
    const categories: Category[] = (data.category || []).map(item => ({
      id: item.value,
      name: item.label,
      type: 'expense',
    }));
    return { accounts, categories };
  }

  /**
   * Create a new income transaction
   */
  async createIncomeTransaction(
    transaction: CreateIncomeTransactionInput
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/income/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for income creation, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/income/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(transaction),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new expense transaction
   */
  async createExpenseTransaction(
    transaction: CreateExpenseTransactionInput
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/expense/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for expense creation, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/expense/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(transaction),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update an income transaction
   */
  async updateIncomeTransaction(
    id: number,
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/income/${id}/`, {
      method: 'PATCH',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for income update, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/income/${id}/`, {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(transaction),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update an expense transaction
   */
  async updateExpenseTransaction(
    id: number,
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/expense/${id}/`, {
      method: 'PATCH',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for expense update, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/expense/${id}/`, {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(transaction),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Delete an income transaction
   */
  async deleteIncomeTransaction(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/income/${id}/`, {
      method: 'DELETE',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(
        `Failed to delete income transaction: ${response.status}`
      );
    }
  }

  /**
   * Delete an expense transaction
   */
  async deleteExpenseTransaction(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/expense/${id}/`, {
      method: 'DELETE',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(
        `Failed to delete expense transaction: ${response.status}`
      );
    }
  }

  /**
   * Get all budgets
   */
  async getBudgets(): Promise<Budget[]> {
    const response = await fetch(`${this.baseUrl}/budget/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ rows: Budget[] }>(response);
    return data.rows || [];
  }

  /**
   * Get budget progress for specific year and month
   */
  async getBudgetDashboard(input: {
    year?: number;
    month?: number | string;
    startDate?: string; // YYYY-MM-DD
    endDate?: string; // YYYY-MM-DD
  }): Promise<{
    budgets: Array<{
      category: string;
      budget: number;
      spent: number;
      percentage: number;
      remaining: number;
      year: number;
      month: number;
    }>;
  }> {
    const url = new URL(
      `${this.baseUrl}/budget/progress/`,
      window.location.origin
    );
    if (input.year) url.searchParams.append('year', String(input.year));
    if (input.month !== undefined && input.month !== null)
      url.searchParams.append('month', String(input.month));
    if (input.startDate) url.searchParams.append('start_date', input.startDate);
    if (input.endDate) url.searchParams.append('end_date', input.endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
  }
}

export const transactionsApiService = new TransactionsApiService();
