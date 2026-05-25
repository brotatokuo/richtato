import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface StatementInstitution {
  id: string;
  slug: string;
  display_name: string;
  account_types: string[];
  file_types: string[];
}

export interface StatementImportRow {
  row_number: number;
  posted_date: string;
  description: string;
  amount: string;
  transaction_type: 'debit' | 'credit';
  institution: string;
  source_file_hash: string;
  source_row_hash: string;
  account_hint: string;
  statement_period: string;
  activity_type: string;
  symbol: string;
  quantity: string;
  status: 'new' | 'duplicate' | 'possible_changed';
}

export interface StatementImportResult {
  parsed_count: number;
  imported_count: number;
  duplicate_count: number;
  invalid_count: number;
  possible_changed_count: number;
  errors: string[];
  file_hash: string;
  institution: string;
  statement_status: 'provisional' | 'closed';
  rows: StatementImportRow[];
  balance_summary?: {
    beginning_balance: string;
    ending_balance: string;
    beginning_date?: string;
    ending_date?: string;
  };
  reconciliation?: {
    statement_internal_ok?: boolean;
    statement_internal_discrepancy?: string;
    computed_ending_balance?: string;
    statement_ending_balance?: string;
    net_activity?: string;
    running_balance_errors?: string[];
    opening_balance_action?:
      | 'none'
      | 'available_create'
      | 'available_update'
      | 'matched'
      | 'create'
      | 'update';
    statement_beginning_balance?: string;
    statement_beginning_date?: string;
    account_opening_balance_current?: string;
    account_opening_balance_date_current?: string;
    opening_balance_amount?: string;
    opening_balance_previous_amount?: string;
    opening_balance_date?: string;
    opening_balance_applied?: boolean;
    account_balance?: string;
    account_ending_discrepancy?: string;
    account_ending_ok?: boolean;
  };
  reconciliation_warnings?: string[];
}

export interface StatementImportInput {
  file: File;
  account: number;
  institution: string;
  statementPeriod?: string;
  statementStatus: 'provisional' | 'closed';
  mode: 'preview' | 'commit';
  applyOpeningBalance?: boolean;
}

class StatementImportService {
  async getInstitutions(): Promise<StatementInstitution[]> {
    const response = await fetch(`${API_BASE}/accounts/import-statement/`, {
      method: 'GET',
      credentials: 'include',
    });
    const data = await this.handleResponse<{
      institutions: StatementInstitution[];
    }>(response);
    return data.institutions;
  }

  async submitStatement(
    input: StatementImportInput
  ): Promise<StatementImportResult> {
    const formData = new FormData();
    formData.append('file', input.file);
    formData.append('account', String(input.account));
    formData.append('institution', input.institution);
    formData.append('statement_period', input.statementPeriod ?? '');
    formData.append('statement_status', input.statementStatus);
    formData.append('mode', input.mode);
    if (input.mode === 'commit' && input.applyOpeningBalance) {
      formData.append('apply_opening_balance', 'true');
    }

    const csrfToken = await csrfService.getCSRFToken();
    let response = await fetch(`${API_BASE}/accounts/import-statement/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData,
    });

    if (response.status === 403) {
      const refreshedToken = await csrfService.refreshToken();
      response = await fetch(`${API_BASE}/accounts/import-statement/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': refreshedToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData,
      });
    }

    return this.handleResponse<StatementImportResult>(response);
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
}

export const statementImportService = new StatementImportService();
