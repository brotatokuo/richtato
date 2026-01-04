/**
 * Annual Analysis API service for comprehensive yearly spending analysis
 */

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

class AnnualAnalysisApiService {
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
   * Get comprehensive annual analysis data
   */
  async getAnnualAnalysis(year?: number): Promise<AnnualAnalysisData> {
    const url = new URL(
      `${this.baseUrl}/annual-analysis/`,
      window.location.origin
    );
    if (year) url.searchParams.append('year', String(year));

    const response = await fetch(url.toString(), {
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
    const response = await fetch(`${this.baseUrl}/annual-analysis/years/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    const data = await this.handleResponse<{ years: number[] }>(response);
    return data.years || [];
  }
}

export const annualAnalysisApiService = new AnnualAnalysisApiService();
