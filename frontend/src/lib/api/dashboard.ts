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

export interface BudgetProgressData {
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
    this.baseUrl = 'http://localhost:8000/api/dashboard';
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
  async getIncomeExpensesData(): Promise<CashFlowData> {
    const response = await fetch(`${this.baseUrl}/income-expenses/`, {
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
  async getBudgetProgressData(): Promise<BudgetProgressData[]> {
    const response = await fetch(`${this.baseUrl}/budget-progress/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<BudgetProgressData[]>(response);
  }

  /**
   * Get expense categories data
   */
  async getExpenseCategoriesData(): Promise<ExpenseCategoriesData> {
    const response = await fetch(`${this.baseUrl}/expense-categories/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<ExpenseCategoriesData>(response);
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
