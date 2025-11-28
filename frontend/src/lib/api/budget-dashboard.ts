/**
 * Budget Dashboard API service for budget-related analytics
 */

export interface ExpenseCategoriesData {
  labels: string[];
  datasets: Array<{
    label?: string;
    data: number[];
    backgroundColor: string[];
  }>;
  start_date?: string;
  end_date?: string;
}

export interface BudgetProgressData {
  budgets: Array<{
    category: string;
    spent: number;
    budget: number;
    percentage: number;
    remaining: number;
    year: number;
    month: number;
  }>;
  start_date: string;
  end_date: string;
}

class BudgetDashboardApiService {
  private baseUrl: string;

  constructor() {
    const root = import.meta.env.VITE_API_BASE_URL || '/api';
    this.baseUrl = `${root}/budget-dashboard`;
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
   * Get expense categories data
   */
  async getExpenseCategoriesData(params?: {
    startDate?: string;
    endDate?: string;
    year?: number;
    month?: number;
  }): Promise<ExpenseCategoriesData> {
    const url = new URL(
      `${this.baseUrl}/expense-categories/`,
      window.location.origin
    );
    if (params?.startDate)
      url.searchParams.append('start_date', params.startDate);
    if (params?.endDate) url.searchParams.append('end_date', params.endDate);
    if (params?.year) url.searchParams.append('year', String(params.year));
    if (params?.month) url.searchParams.append('month', String(params.month));
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<ExpenseCategoriesData>(response);
  }

  /**
   * Get budget progress data for a date range
   */
  async getBudgetProgress(params?: {
    year?: number;
    month?: number | string;
    startDate?: string;
    endDate?: string;
  }): Promise<BudgetProgressData> {
    const url = new URL(`${this.baseUrl}/progress/`, window.location.origin);
    if (params?.year) url.searchParams.append('year', String(params.year));
    if (params?.month !== undefined && params?.month !== null)
      url.searchParams.append('month', String(params.month));
    if (params?.startDate)
      url.searchParams.append('start_date', params.startDate);
    if (params?.endDate) url.searchParams.append('end_date', params.endDate);
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<BudgetProgressData>(response);
  }

  /**
   * Get budget rankings
   */
  async getBudgetRankings(params?: {
    year?: number;
    month?: string;
    count?: number;
  }): Promise<{ category_rankings: any[] }> {
    const url = new URL(`${this.baseUrl}/rankings/`, window.location.origin);
    if (params?.year) url.searchParams.append('year', String(params.year));
    if (params?.month) url.searchParams.append('month', params.month);
    if (params?.count) url.searchParams.append('count', String(params.count));
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<{ category_rankings: any[] }>(response);
  }

  /**
   * Get expense years
   */
  async getExpenseYears(): Promise<number[]> {
    const response = await fetch(`${this.baseUrl}/expense-years/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{ years: number[] }>(response);
    return data.years || [];
  }
}

export const budgetDashboardApiService = new BudgetDashboardApiService();
