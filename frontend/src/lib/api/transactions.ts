/**
 * Transactions API service for fetching transaction data
 */
import { csrfService } from './csrf';

export interface Transaction {
  id: number;
  account: number;
  account_name: string;
  date: string;
  amount: number;
  signed_amount: number;
  description: string;
  transaction_type: 'debit' | 'credit';
  transaction_type_display: string;
  category: number | null;
  category_name: string | null;
  merchant: number | null;
  merchant_name: string | null;
  status: string;
  is_recurring: boolean;
  sync_source: string;
  categorization_status: string;
  categorization_status_display: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTransactionInput {
  account_id: number;
  date: string; // YYYY-MM-DD
  amount: number;
  description: string;
  transaction_type: 'debit' | 'credit';
  category_id?: number;
  merchant_name?: string;
  status?: 'pending' | 'posted' | 'reconciled';
}

export interface Account {
  id: number;
  name: string;
  type: string;
  type_display?: string;
  balance?: number;
  entity?: string;
  entity_display?: string;
  date?: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  parent?: number;
  parent_name?: string;
  full_path?: string;
  icon?: string;
  color?: string;
  is_income: boolean;
  is_expense: boolean;
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
   * Get transactions with optional filters
   */
  async getTransactions(input?: {
    limit?: number;
    startDate?: string; // YYYY-MM-DD
    endDate?: string; // YYYY-MM-DD
    type?: 'debit' | 'credit'; // debit = expense, credit = income
    accountId?: number;
    categoryId?: number;
    search?: string;
  }): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/transactions/`, window.location.origin);
    if (input?.startDate) url.searchParams.append('start_date', input.startDate);
    if (input?.endDate) url.searchParams.append('end_date', input.endDate);
    if (input?.type) url.searchParams.append('type', input.type);
    if (input?.accountId) url.searchParams.append('account_id', String(input.accountId));
    if (input?.categoryId) url.searchParams.append('category_id', String(input.categoryId));
    if (input?.search) url.searchParams.append('search', input.search);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ transactions: Transaction[] }>(response);
    return data.transactions || [];
  }

  /**
   * Get income transactions (credits)
   */
  async getIncomeTransactions(input?: {
    limit?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<Transaction[]> {
    return this.getTransactions({
      ...input,
      type: 'credit',
    });
  }

  /**
   * Get expense transactions (debits)
   */
  async getExpenseTransactions(input?: {
    limit?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<Transaction[]> {
    return this.getTransactions({
      ...input,
      type: 'debit',
    });
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
  async getCategories(includeGlobal: boolean = true): Promise<Category[]> {
    const url = new URL(`${this.baseUrl}/transactions/categories/`, window.location.origin);
    url.searchParams.append('include_global', String(includeGlobal));

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ categories: Category[] }>(response);
    return data.categories || [];
  }

  /**
   * Create a new transaction
   */
  async createTransaction(transaction: CreateTransactionInput): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/transactions/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for transaction creation, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/transactions/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(transaction),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Create a new income transaction (credit)
   */
  async createIncomeTransaction(input: {
    account_id: number;
    date: string;
    amount: number;
    description: string;
    category_id?: number;
  }): Promise<Transaction> {
    return this.createTransaction({
      ...input,
      transaction_type: 'credit',
    });
  }

  /**
   * Create a new expense transaction (debit)
   */
  async createExpenseTransaction(input: {
    account_id: number;
    date: string;
    amount: number;
    description: string;
    category_id?: number;
  }): Promise<Transaction> {
    return this.createTransaction({
      ...input,
      transaction_type: 'debit',
    });
  }

  /**
   * Update a transaction
   */
  async updateTransaction(
    id: number,
    updates: Partial<{
      date: string;
      amount: number;
      description: string;
      transaction_type: 'debit' | 'credit';
      category_id: number | null;
      merchant_name: string;
      status: string;
    }>
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/transactions/${id}/`, {
      method: 'PATCH',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(updates),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      console.log('CSRF token invalid for transaction update, refreshing...');
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/transactions/${id}/`, {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(updates),
      });
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Delete a transaction
   */
  async deleteTransaction(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/transactions/${id}/`, {
      method: 'DELETE',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete transaction: ${response.status}`);
    }
  }

  /**
   * Categorize a transaction
   */
  async categorizeTransaction(
    transactionId: number,
    categoryId: number
  ): Promise<Transaction> {
    let response = await fetch(
      `${this.baseUrl}/transactions/${transactionId}/categorize/`,
      {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({ category_id: categoryId }),
      }
    );

    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(
        `${this.baseUrl}/transactions/${transactionId}/categorize/`,
        {
          method: 'POST',
          headers: await csrfService.getHeaders(),
          credentials: 'include',
          body: JSON.stringify({ category_id: categoryId }),
        }
      );
    }

    return this.handleResponse<Transaction>(response);
  }

  /**
   * Get transaction summary for a date range
   */
  async getTransactionSummary(startDate: string, endDate: string): Promise<{
    total_income: number;
    total_expenses: number;
    net: number;
    transaction_count: number;
  }> {
    const url = new URL(`${this.baseUrl}/transactions/summary/`, window.location.origin);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
  }

  /**
   * Get uncategorized transactions
   */
  async getUncategorizedTransactions(limit: number = 100): Promise<Transaction[]> {
    const url = new URL(`${this.baseUrl}/transactions/uncategorized/`, window.location.origin);
    url.searchParams.append('limit', String(limit));

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ transactions: Transaction[] }>(response);
    return data.transactions || [];
  }

  /**
   * Get all budgets
   */
  async getBudgets(): Promise<Budget[]> {
    const response = await fetch(`${this.baseUrl}/budgets/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ budgets: Budget[] }>(response);
    return data.budgets || [];
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
      `${this.baseUrl}/budgets/progress/`,
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

  /**
   * Get account field choices (types and entities)
   */
  async getAccountFieldChoices(): Promise<{
    type: Array<{ value: string; label: string }>;
    entity: Array<{ value: string; label: string }>;
  }> {
    const response = await fetch(`${this.baseUrl}/accounts/field-choices/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
  }
}

export const transactionsApiService = new TransactionsApiService();
