/**
 * Annual Analysis API service for comprehensive yearly spending analysis
 */
import { BaseApiClient } from './base-client';

import { fetchWithAuth } from './fetchClient';

export interface MonthlyBreakdown {
  month: string;
  month_num: number;
  essential: number;
  non_essential: number;
  total: number;
}

export interface CategoryBreakdown {
  name: string;
  amount: number;
  is_essential: boolean;
  color: string;
  icon: string;
}

export interface IncomeSource {
  name: string;
  amount: number;
  color: string;
}

export interface AnnualAnalysisData {
  year: number;
  total_income: number;
  total_expenses: number;
  essential_total: number;
  non_essential_total: number;
  monthly_breakdown: MonthlyBreakdown[];
  category_breakdown: CategoryBreakdown[];
  income_sources: IncomeSource[];
}

class AnnualAnalysisApiService extends BaseApiClient {
  constructor() {
    super('/budget-dashboard');
  }

  /**
   * Get comprehensive annual analysis data
   */
  async getAnnualAnalysis(year?: number): Promise<AnnualAnalysisData> {
    const url = new URL(
      `${this.baseUrl}/annual-analysis/`,
      window.location.origin
    );
    if (year) url.searchParams.append('year', String(year));

    const response = await fetchWithAuth(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    return this.handleResponse<AnnualAnalysisData>(response);
  }

  /**
   * Get available years with transaction data
   */
  async getAvailableYears(): Promise<number[]> {
    const response = await fetchWithAuth(
      `${this.baseUrl}/annual-analysis/years/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      }
    );
    const data = await this.handleResponse<{ years: number[] }>(response);
    return data.years || [];
  }
}

export const annualAnalysisApiService = new AnnualAnalysisApiService();
