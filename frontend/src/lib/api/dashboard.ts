/**
 * Dashboard API service for fetching dashboard metrics and data
 */

export interface DashboardData {
  networth: string;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  budget_utilization_30_days: string;
  nonessential_spending_pct: string;
}

export interface CashFlowData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    borderRadius?: number;
    fill?: boolean;
    tension?: number;
    type?: string;
  }>;
}

export interface BudgetDashboardData {
  category: string;
  spent: number;
  budget: number;
  percentage: number;
  remaining: number;
}

export interface ExpenseCategoriesData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor: string[];
  }>;
}

class DashboardApiService {
  private baseUrl: string;

  constructor() {
    const root = import.meta.env.VITE_API_BASE_URL || '/api';
    this.baseUrl = `${root}/dashboard`;
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
   * Get dashboard metrics (net worth, savings rate, etc.)
   */
  async getDashboardMetrics(): Promise<DashboardData> {
    const response = await fetch(`${this.baseUrl}/metrics/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<DashboardData>(response);
  }

  /**
   * Get cash flow data for the last 6 months
   */
  async getCashFlowData(period: string = '6m'): Promise<CashFlowData> {
    const response = await fetch(
      `${this.baseUrl}/cash-flow/?period=${period}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

    return this.handleResponse<CashFlowData>(response);
  }

  /**
   * Get income vs expenses data for the last 6 months
   */
  async getIncomeExpensesData(params?: {
    startDate?: string;
    endDate?: string;
  }): Promise<CashFlowData> {
    const url = new URL(
      `${this.baseUrl}/income-expenses/`,
      window.location.origin
    );
    if (params?.startDate)
      url.searchParams.append('start_date', params.startDate);
    if (params?.endDate) url.searchParams.append('end_date', params.endDate);
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<CashFlowData>(response);
  }

  /**
   * Get savings data for the last 6 months
   */
  async getSavingsData(): Promise<CashFlowData> {
    const response = await fetch(`${this.baseUrl}/savings/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<CashFlowData>(response);
  }

  /**
   * Get budget progress data for current month
   */
  async getBudgetDashboardData(
    year?: number,
    month?: number | string
  ): Promise<any> {
    const url = new URL(
      `${this.baseUrl}/budget-progress/`,
      window.location.origin
    );
    if (year) url.searchParams.append('year', String(year));
    if (month !== undefined && month !== null)
      url.searchParams.append('month', String(month));
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<any>(response);
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

  /**
   * Get expense categories data
   */
  async getExpenseCategoriesData(params?: {
    startDate?: string;
    endDate?: string;
    year?: number;
    month?: number;
  }): Promise<
    ExpenseCategoriesData & { start_date?: string; end_date?: string }
  > {
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

    return this.handleResponse<
      ExpenseCategoriesData & { start_date?: string; end_date?: string }
    >(response);
  }

  /**
   * Get top spending categories
   */
  async getTopCategoriesData(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/top-categories/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<any>(response);
  }
}

export const dashboardApiService = new DashboardApiService();
