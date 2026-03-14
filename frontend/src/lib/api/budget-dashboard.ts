/**
 * Budget Dashboard API service for budget-related analytics
 */

import { fetchWithAuth } from './fetchClient';

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

export interface MonthlyBudgetData {
  year: number;
  month: number;
  month_name: string;
  label: string;
  total_budget: number;
  total_spent: number;
  total_remaining: number;
  percentage: number;
  categories: Array<{
    category: string;
    spent: number;
    budget: number;
    percentage: number;
    remaining: number;
  }>;
  start_date: string;
  end_date: string;
}

export interface MultiMonthBudgetProgressData {
  monthly_data: MonthlyBudgetData[];
  months_requested: number;
}

class BudgetDashboardApiService {
  private baseUrl: string;

  constructor() {
    const root = import.meta.env.VITE_API_BASE_URL || '/api/v1';
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
    const response = await fetchWithAuth(url.toString(), {
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
    const response = await fetchWithAuth(url.toString(), {
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
  }): Promise<{ category_rankings: Array<{ category: string; amount: number; rank: number }> }> {
    const url = new URL(`${this.baseUrl}/rankings/`, window.location.origin);
    if (params?.year) url.searchParams.append('year', String(params.year));
    if (params?.month) url.searchParams.append('month', params.month);
    if (params?.count) url.searchParams.append('count', String(params.count));
    const response = await fetchWithAuth(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<{ category_rankings: Array<{ category: string; amount: number; rank: number }> }>(response);
  }

  /**
   * Get expense years
   */
  async getExpenseYears(): Promise<number[]> {
    const response = await fetchWithAuth(`${this.baseUrl}/expense-years/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{ years: number[] }>(response);
    return data.years || [];
  }

  /**
   * Get budget progress for multiple months (for timeline and trends)
   */
  async getBudgetProgressMultiMonth(params?: {
    months?: number;
  }): Promise<MultiMonthBudgetProgressData> {
    const url = new URL(
      `${this.baseUrl}/progress/multi-month/`,
      window.location.origin
    );
    if (params?.months) url.searchParams.append('months', String(params.months));
    const response = await fetchWithAuth(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<MultiMonthBudgetProgressData>(response);
  }
}

export const budgetDashboardApiService = new BudgetDashboardApiService();
