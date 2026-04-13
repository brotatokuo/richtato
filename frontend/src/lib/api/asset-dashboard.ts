/**
 * Asset Dashboard API service for asset/networth-related analytics
 */
import { BaseApiClient } from './base-client';

export interface AssetDashboardData {
  networth: number;
  total_assets: number;
  total_liabilities: number;
  networth_growth: string;
  networth_growth_class: string;
  savings_rate: string;
  savings_rate_class: string;
  savings_rate_context: string;
  expense_sum: number;
  income_sum: number;
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

export interface NetWorthHistoryPoint {
  date: string;
  networth: number;
  assets: number;
  liabilities: number;
}

export interface NetWorthHistoryData {
  history: NetWorthHistoryPoint[];
}

export interface AccountBreakdownItem {
  type: string;
  type_display: string;
  total: number;
  count: number;
  is_liability: boolean;
}

export interface AccountBreakdownData {
  breakdown: AccountBreakdownItem[];
}

class AssetDashboardApiService extends BaseApiClient {
  constructor() {
    super('/asset-dashboard');
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
  async getTopCategoriesData(): Promise<unknown> {
    const response = await fetch(`${this.baseUrl}/top-categories/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<unknown>(response);
  }

  /**
   * Get Sankey diagram data
   */
  async getSankeyData(): Promise<unknown> {
    const response = await fetch(`${this.baseUrl}/sankey-data/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<unknown>(response);
  }

  /**
   * Get net worth history over time
   */
  async getNetWorthHistory(
    period: '1m' | '3m' | '6m' | '1y' | 'all' = '6m'
  ): Promise<NetWorthHistoryData> {
    const response = await fetch(
      `${this.baseUrl}/networth-history/?period=${period}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );

    return this.handleResponse<NetWorthHistoryData>(response);
  }

  /**
   * Get account balances grouped by type
   */
  async getAccountBreakdown(): Promise<AccountBreakdownData> {
    const response = await fetch(`${this.baseUrl}/account-breakdown/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<AccountBreakdownData>(response);
  }
}

export const assetDashboardApiService = new AssetDashboardApiService();
