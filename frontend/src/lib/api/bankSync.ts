import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export type SyncMode = 'auto' | 'upload' | 'manual';

export type AgentCadence = 'manual' | 'daily' | 'weekly' | 'monthly';

export type AgentFlow = 'deposit' | 'credit_card' | 'investment_balance';

export interface BankSyncSetupAccount {
  id: number;
  name: string;
  institution_slug: string | null;
  institution_name: string;
  account_type: string;
  account_type_display: string;
  sync_mode: SyncMode;
  agent_cadence: AgentCadence;
  agent_sync_hour: number;
  agent_sync_supported: boolean;
  agent_flow: AgentFlow | null;
  needs_storage_for_auto: boolean;
  has_storage_uri: boolean;
  resolved_storage_uri: string;
  activity_url: string;
  has_activity_url: boolean;
  needs_activity_url_for_auto: boolean;
}

export interface BankAgentConfigAccount {
  name: string;
  flow: AgentFlow;
  storage_uri: string;
  richtato_account_id: number;
  activity_url?: string;
}

export interface BankAgentConfigLogin {
  institution: string;
  nickname: string;
  cadence: AgentCadence;
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
  duplicate_institution_logins: string[];
}

export const AGENT_CADENCE_OPTIONS: Array<{
  value: AgentCadence;
  label: string;
}> = [
  { value: 'manual', label: 'On demand' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

export const AGENT_HOUR_OPTIONS = Array.from({ length: 24 }, (_, hour) => ({
  value: hour,
  label: `${hour.toString().padStart(2, '0')}:00`,
}));

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
              : typeof errorData.agent_cadence === 'string'
                ? errorData.agent_cadence
                : Array.isArray(errorData.agent_cadence)
                  ? errorData.agent_cadence.join(', ')
                  : typeof errorData.agent_activity_url === 'string'
                    ? errorData.agent_activity_url
                    : Array.isArray(errorData.agent_activity_url)
                      ? errorData.agent_activity_url.join(', ')
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

  async updateAccountSchedule(
    accountId: number,
    input: { agent_cadence: AgentCadence; agent_sync_hour: number }
  ): Promise<void> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/${accountId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify(input),
      }
    );
    await this.handleResponse(response);
  }

  async updateActivityUrl(
    accountId: number,
    activityUrl: string
  ): Promise<void> {
    const response = await csrfService.fetchWithCsrf(
      `${API_BASE}/accounts/${accountId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify({ agent_activity_url: activityUrl }),
      }
    );
    await this.handleResponse(response);
  }

  async getSetupYamlText(): Promise<string> {
    const response = await fetch(
      `${API_BASE}/accounts/bank-agent-setup-export/`,
      {
        credentials: 'include',
      }
    );
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const message =
        typeof errorData.error === 'string'
          ? errorData.error
          : `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }
    return response.text();
  }

  async downloadSetupYaml(): Promise<void> {
    const yamlText = await this.getSetupYamlText();
    const blob = new Blob([yamlText], { type: 'text/yaml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'richtato-bank-agent-setup.yml';
    anchor.click();
    URL.revokeObjectURL(url);
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
