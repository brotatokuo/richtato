/**
 * Transactions API service for fetching income and expense data
 */

export interface Transaction {
  id: number;
  description: string;
  date: string;
  amount: number;
  Account?: string;
  Category?: string;
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
    const url = new URL(
      `${this.baseUrl}/income/api/incomes/`,
      window.location.origin
    );
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
    const url = new URL(
      `${this.baseUrl}/expense/api/expenses/`,
      window.location.origin
    );
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
    const response = await fetch(`${this.baseUrl}/accounts/api/accounts/`, {
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
      `${this.baseUrl}/accounts/api/accounts/${accountId}/transactions/`,
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
    const response = await fetch(
      `${this.baseUrl}/accounts/api/accounts/details/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      }
    );
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
      `${this.baseUrl}/accounts/api/accounts/${accountId}/transactions/`,
      {
        method: 'PATCH',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      }
    );
    return this.handleResponse(response);
  }

  async deleteAccountTransaction(accountId: number, id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/accounts/api/accounts/${accountId}/transactions/`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
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
    const response = await fetch(`${this.baseUrl}/accounts/api/accounts/`, {
      method: 'POST',
      headers: this.getHeaders(),
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
    const response = await fetch(
      `${this.baseUrl}/accounts/api/accounts/${id}/`,
      {
        method: 'PATCH',
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      }
    );

    return this.handleResponse<Account>(response);
  }

  /**
   * Delete an account
   */
  async deleteAccount(id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/accounts/api/accounts/${id}/`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

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
   * Create a new income transaction
   */
  async createIncomeTransaction(
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    const response = await fetch(`${this.baseUrl}/incomes/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new expense transaction
   */
  async createExpenseTransaction(
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    const response = await fetch(`${this.baseUrl}/expenses/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update an income transaction
   */
  async updateIncomeTransaction(
    id: number,
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    const response = await fetch(`${this.baseUrl}/incomes/${id}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Update an expense transaction
   */
  async updateExpenseTransaction(
    id: number,
    transaction: Partial<Transaction>
  ): Promise<Transaction> {
    const response = await fetch(`${this.baseUrl}/expenses/${id}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Delete an income transaction
   */
  async deleteIncomeTransaction(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/incomes/${id}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
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
    const response = await fetch(`${this.baseUrl}/expenses/${id}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
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
