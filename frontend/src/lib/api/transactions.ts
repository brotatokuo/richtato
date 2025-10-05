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
    this.baseUrl = 'http://localhost:8000/api';
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
  async getIncomeTransactions(limit?: number): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/income/api/incomes/`);
    if (limit) {
      url.searchParams.append('limit', limit.toString());
    }

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
  async getExpenseTransactions(limit?: number): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/expense/api/expenses/`);
    if (limit) {
      url.searchParams.append('limit', limit.toString());
    }

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
}

export const transactionsApiService = new TransactionsApiService();
