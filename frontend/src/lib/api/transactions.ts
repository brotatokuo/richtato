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
  category_type:
    | 'income'
    | 'expense'
    | 'transfer'
    | 'investment'
    | 'other'
    | 'uncategorized';
  status: string;
  is_recurring: boolean;
  sync_source: string;
  categorization_status: string;
  categorization_status_display: string;
  created_at: string;
  updated_at: string;
  notes?: string | null;
}

export interface CreateTransactionInput {
  account_id: number;
  date: string; // YYYY-MM-DD
  amount: number;
  description: string;
  transaction_type: 'debit' | 'credit';
  category_id?: number;
  status?: 'pending' | 'posted' | 'reconciled';
  notes?: string | null;
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
  // Account type
  account_type?: string;
  account_type_display?: string;
  account_number_last4?: string;
  institution_name?: string;
  currency?: string;
  is_active?: boolean;
  // Card customization
  image_key?: string | null;
  // Sync connection fields
  sync_source?: string;
  has_connection?: boolean;
  connection_id?: number | null;
  connection_status?: 'active' | 'disconnected' | 'error' | null;
  last_sync?: string | null;
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
  type: 'income' | 'expense' | 'transfer' | 'investment' | 'other';
  type_display?: string;
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

  /** Paginated transactions response */
  async getTransactions(input?: {
    page?: number;
    pageSize?: number;
    startDate?: string; // YYYY-MM-DD
    endDate?: string; // YYYY-MM-DD
    type?: 'debit' | 'credit'; // debit = expense, credit = income
    accountId?: number;
    categoryId?: number;
    search?: string;
  }): Promise<{
    transactions: Transaction[];
    page?: number;
    page_size?: number;
    total_count?: number;
    has_next?: boolean;
  }> {
    const url = new URL(
      `${this.baseUrl}/transactions/`,
      window.location.origin
    );
    if (input?.page) url.searchParams.append('page', String(input.page));
    if (input?.pageSize)
      url.searchParams.append('page_size', String(input.pageSize));
    if (input?.startDate)
      url.searchParams.append('start_date', input.startDate);
    if (input?.endDate) url.searchParams.append('end_date', input.endDate);
    if (input?.type) url.searchParams.append('type', input.type);
    if (input?.accountId)
      url.searchParams.append('account_id', String(input.accountId));
    if (input?.categoryId)
      url.searchParams.append('category_id', String(input.categoryId));
    if (input?.search) url.searchParams.append('search', input.search);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{
      transactions: Transaction[];
      page?: number;
      page_size?: number;
      total_count?: number;
      has_next?: boolean;
    }>(response);
    return {
      transactions: data.transactions || [],
      page: data.page,
      page_size: data.page_size,
      total_count: data.total_count,
      has_next: data.has_next,
    };
  }

  /**
   * Get filter options for transaction table columns
   */
  async getFilterOptions(input?: {
    startDate?: string;
    endDate?: string;
    type?: 'debit' | 'credit';
    accountId?: number;
    categoryId?: number;
  }): Promise<{
    dates: Array<{ label: string; value: string; count: number }>;
    category_types: Array<{ label: string; value: string; count: number }>;
    categories: Array<{ label: string; value: string; count: number }>;
    accounts: Array<{ label: string; value: string; count: number }>;
    amounts: Array<{ label: string; value: string; count: number }>;
    descriptions: Array<{ label: string; value: string; count: number }>;
  }> {
    const url = new URL(
      `${this.baseUrl}/transactions/filter-options/`,
      window.location.origin
    );
    if (input?.startDate)
      url.searchParams.append('start_date', input.startDate);
    if (input?.endDate) url.searchParams.append('end_date', input.endDate);
    if (input?.type) url.searchParams.append('type', input.type);
    if (input?.accountId)
      url.searchParams.append('account_id', String(input.accountId));
    if (input?.categoryId)
      url.searchParams.append('category_id', String(input.categoryId));

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  /**
   * Get income transactions (credits). Returns full paginated response.
   */
  async getIncomeTransactions(input?: {
    page?: number;
    pageSize?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<{
    transactions: Transaction[];
    page?: number;
    page_size?: number;
    total_count?: number;
    has_next?: boolean;
  }> {
    return this.getTransactions({
      ...input,
      type: 'credit',
    });
  }

  /**
   * Get expense transactions (debits). Returns full paginated response.
   */
  async getExpenseTransactions(input?: {
    page?: number;
    pageSize?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<{
    transactions: Transaction[];
    page?: number;
    page_size?: number;
    total_count?: number;
    has_next?: boolean;
  }> {
    return this.getTransactions({
      ...input,
      type: 'debit',
    });
  }

  /**
   * Get balance history for an account
   */
  async getAccountBalanceHistory(
    accountId: number,
    input?: { days?: number }
  ): Promise<{
    current_balance: number;
    starting_balance: number;
    change: number;
    change_percent: number;
    data_points: Array<{ date: string; balance: number }>;
  }> {
    const url = new URL(
      `${this.baseUrl}/accounts/${accountId}/balance-history/`,
      window.location.origin
    );
    if (input?.days) url.searchParams.append('days', String(input.days));

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse(response);
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
   * Get transactions for an account
   */
  async getAccountTransactions(
    accountId: number,
    input?: {
      page?: number;
      pageSize?: number;
    }
  ): Promise<{
    columns: Array<{ field: string; title: string }>;
    rows: Array<{
      id: number;
      date: string;
      description: string;
      amount: string;
      transaction_type: 'credit' | 'debit';
    }>;
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
  }): Promise<{ id: number; amount: string; date: string }> {
    const response = await fetch(`${this.baseUrl}/accounts/details/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });
    return this.handleResponse<{ id: number; amount: string; date: string }>(response);
  }

  async updateAccountTransaction(
    accountId: number,
    input: {
      id: number;
      amount?: number;
      date?: string;
    }
  ): Promise<{ id: number; amount: string; date: string }> {
    const response = await fetch(
      `${this.baseUrl}/accounts/${accountId}/transactions/`,
      {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      }
    );
    return this.handleResponse<{ id: number; amount: string; date: string }>(response);
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
    institution_slug?: string;
    asset_entity_name?: string;
  }): Promise<Account> {
    let response = await fetch(`${this.baseUrl}/accounts/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({
        name: input.name,
        account_type: input.type,
        institution_slug: input.institution_slug,
      }),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/accounts/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({
          name: input.name,
          account_type: input.type,
          institution_slug: input.institution_slug,
        }),
      });
    }

    return this.handleResponse<Account>(response);
  }

  /**
   * Update an account
   */
  async updateAccount(
    id: number,
    input: Partial<{
      name: string;
      type: string;
      asset_entity_name: string;
      image_key: string | null;
    }>
  ): Promise<Account> {
    let response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
      method: 'PATCH',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(input),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(input),
      });
    }

    return this.handleResponse<Account>(response);
  }

  /**
   * Delete an account
   */
  async deleteAccount(id: number): Promise<void> {
    let response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
      method: 'DELETE',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/accounts/${id}/`, {
        method: 'DELETE',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
      });
    }

    if (!response.ok) {
      throw new Error(`Failed to delete account: ${response.status}`);
    }
  }

  /**
   * Get all categories for the current user
   */
  async getCategories(): Promise<Category[]> {
    const response = await fetch(
      `${this.baseUrl}/transactions/categories/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

    const data = await this.handleResponse<{ categories: Category[] }>(
      response
    );
    return data.categories || [];
  }

  /**
   * Create a new transaction
   */
  async createTransaction(
    transaction: CreateTransactionInput
  ): Promise<Transaction> {
    let response = await fetch(`${this.baseUrl}/transactions/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(transaction),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
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
      status: string;
      notes: string | null;
    }>
  ): Promise<Transaction> {
    const doPatch = async () =>
      fetch(`${this.baseUrl}/transactions/${id}/`, {
        method: 'PATCH',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(updates),
      });

    let response = await doPatch();

    // If CSRF token is invalid, clear + refresh and retry once
    if (response.status === 403) {
      csrfService.clearToken();
      await csrfService.refreshToken();
      response = await doPatch();
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
   * Get cashflow summary (income/expense/investment by category) for a date range.
   * Uses server-side aggregation - no raw transactions fetched.
   */
  async getCashflowSummary(startDate: string, endDate: string): Promise<{
    total_income: number;
    total_expenses: number;
    total_investments: number;
    net_savings: number;
    income_by_category: Record<string, number>;
    expenses_by_category: Record<string, number>;
    investments_by_category: Record<string, number>;
  }> {
    const url = new URL(
      `${this.baseUrl}/transactions/cashflow-summary/`,
      window.location.origin
    );
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
   * Get transaction summary for a date range
   */
  async getTransactionSummary(
    startDate: string,
    endDate: string
  ): Promise<{
    total_income: number;
    total_expenses: number;
    net: number;
    transaction_count: number;
  }> {
    const url = new URL(
      `${this.baseUrl}/transactions/summary/`,
      window.location.origin
    );
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
  async getUncategorizedTransactions(
    limit: number = 100
  ): Promise<Transaction[]> {
    const url = new URL(
      `${this.baseUrl}/transactions/uncategorized/`,
      window.location.origin
    );
    url.searchParams.append('limit', String(limit));

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    const data = await this.handleResponse<{ transactions: Transaction[] }>(
      response
    );
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
      `${this.baseUrl}/budget-dashboard/progress/`,
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

  /**
   * Start bulk recategorization of all transactions
   */
  async startRecategorization(
    keepExistingForUnmatched: boolean
  ): Promise<{ task_id: number }> {
    let response = await fetch(`${this.baseUrl}/transactions/recategorize/`, {
      method: 'POST',
      headers: await csrfService.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({
        keep_existing_for_unmatched: keepExistingForUnmatched,
      }),
    });

    // If CSRF token is invalid, refresh it and retry once
    if (response.status === 403) {
      await csrfService.refreshToken();
      response = await fetch(`${this.baseUrl}/transactions/recategorize/`, {
        method: 'POST',
        headers: await csrfService.getHeaders(),
        credentials: 'include',
        body: JSON.stringify({
          keep_existing_for_unmatched: keepExistingForUnmatched,
        }),
      });
    }

    return this.handleResponse<{ task_id: number }>(response);
  }

  /**
   * Get recategorization task progress
   */
  async getRecategorizeProgress(taskId: number): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    total: number;
    processed: number;
    updated: number;
    progress_percent: number;
    error: string | null;
  }> {
    const response = await fetch(
      `${this.baseUrl}/transactions/recategorize/${taskId}/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

    return this.handleResponse(response);
  }
}

export const transactionsApiService = new TransactionsApiService();
