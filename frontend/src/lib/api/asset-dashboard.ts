/**
 * Asset Dashboard API service for asset/networth-related analytics
 */

export interface AssetDashboardData {
  networth: string;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  expense_sum: string;
  income_sum: string;
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
    borderDash?: number[];
  }>;
}

class AssetDashboardApiService {
  private baseUrl: string;

  constructor() {
    const root = import.meta.env.VITE_API_BASE_URL || '/api';
    this.baseUrl = `${root}/asset-dashboard`;
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
  async getDashboardMetrics(): Promise<AssetDashboardData> {
    const response = await fetch(`${this.baseUrl}/metrics/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<AssetDashboardData>(response);
  }

  /**
   * Get cash flow data for a specified period
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
   * Get income vs expenses data
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

  /**
   * Get Sankey diagram data
   */
  async getSankeyData(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/sankey-data/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<any>(response);
  }
}

export const assetDashboardApiService = new AssetDashboardApiService();
