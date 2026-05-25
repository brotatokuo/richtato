import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export type SyncMode = 'auto' | 'upload' | 'manual';

export type AgentFlow = 'deposit' | 'credit_card' | 'investment_balance';

export interface BankSyncSetupAccount {
  id: number;
  name: string;
  institution_slug: string | null;
  institution_name: string;
  account_type: string;
  account_type_display: string;
  sync_mode: SyncMode;
  agent_sync_supported: boolean;
  agent_flow: AgentFlow | null;
  needs_storage_for_auto: boolean;
  has_storage_uri: boolean;
  resolved_storage_uri: string;
}

export interface BankAgentConfigAccount {
  name: string;
  flow: AgentFlow;
  storage_uri: string;
  richtato_account_id: number;
}

export interface BankAgentConfigLogin {
  institution: string;
  nickname: string;
  cadence: string;
  hour: number;
  accounts: BankAgentConfigAccount[];
}

export interface BankAgentConfig {
  version: number;
  generated_at: string;
  user_id: number;
  source: string;
  logins: BankAgentConfigLogin[];
}

export interface BankSyncSetupResponse {
  accounts: BankSyncSetupAccount[];
  agent_config: BankAgentConfig;
}

class BankSyncApi {
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const message =
        typeof errorData.error === 'string'
          ? errorData.error
          : typeof errorData.sync_mode === 'string'
            ? errorData.sync_mode
            : Array.isArray(errorData.sync_mode)
              ? errorData.sync_mode.join(', ')
              : `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }
    return response.json();
  }

  async getSetup(): Promise<BankSyncSetupResponse> {
    const response = await fetch(`${API_BASE}/accounts/sync-setup/`, {
      credentials: 'include',
    });
    return this.handleResponse(response);
  }

  async updateSyncMode(accountId: number, syncMode: SyncMode): Promise<void> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/${accountId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify({ sync_mode: syncMode }),
      }
    );
    await this.handleResponse(response);
  }

  async getApiToken(): Promise<{ token: string; fernet_key: string }> {
    const response = await fetch(`${API_BASE}/auth/api-token/`, {
      credentials: 'include',
    });
    return this.handleResponse(response);
  }
}

export const bankSyncApi = new BankSyncApi();

export const SYNC_MODE_OPTIONS: Array<{
  value: SyncMode;
  label: string;
  description: string;
}> = [
  {
    value: 'auto',
    label: 'Auto sync',
    description: 'Host bank-agent downloads statements or scrapes balances.',
  },
  {
    value: 'upload',
    label: 'Statement upload',
    description: 'Import CSV, Excel, or PDF statements manually.',
  },
  {
    value: 'manual',
    label: 'Manual entry',
    description: 'Type transactions and balances yourself.',
  },
];

export function agentFlowLabel(flow: AgentFlow | null): string {
  switch (flow) {
    case 'deposit':
      return 'Statement download';
    case 'credit_card':
      return 'Credit statement download';
    case 'investment_balance':
      return 'Portfolio balance scrape';
    default:
      return 'Not supported';
  }
}
