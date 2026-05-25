export interface LocalAgentAccount {
  id: number;
  login_id: number;
  name: string;
  flow: string;
  storage_uri: string;
  richtato_account_id: number | null;
  enabled: boolean;
  last_success_at: string | null;
  has_activity_url: boolean;
}

export interface LocalAgentLogin {
  id: number;
  institution_slug: string;
  nickname: string;
  status: string;
  cadence: string;
  preferred_run_hour_local: number;
  next_run_at: string | null;
  last_run_at: string | null;
  last_success_at: string | null;
  last_failure_kind: string | null;
  last_failure_reason: string;
  cookies_captured_at: string | null;
  accounts: LocalAgentAccount[];
}

export interface LocalAgentRun {
  id: number;
  login_id: number;
  kind: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  files_downloaded: number;
  error_kind: string | null;
  error: string;
}

export interface LocalAgentStatus {
  ok: boolean;
  reauth_required: boolean;
  login_count: number;
  account_count: number;
  logins: LocalAgentLogin[];
  recent_runs: LocalAgentRun[];
}

export interface LocalAgentActionResponse {
  ok: boolean;
  message?: string;
  error?: string;
  status?: LocalAgentStatus;
}

const DEFAULT_LOCAL_AGENT_URL = 'http://127.0.0.1:8765';
const LOCAL_AGENT_URL_KEY = 'richtato.bankAgent.localUrl';
const LOCAL_AGENT_TOKEN_KEY = 'richtato.bankAgent.localToken';

export function getStoredLocalAgentConnection(): {
  baseUrl: string;
  token: string;
} {
  return {
    baseUrl:
      window.localStorage.getItem(LOCAL_AGENT_URL_KEY) ??
      DEFAULT_LOCAL_AGENT_URL,
    token: window.localStorage.getItem(LOCAL_AGENT_TOKEN_KEY) ?? '',
  };
}

export function storeLocalAgentConnection(input: {
  baseUrl: string;
  token: string;
}) {
  window.localStorage.setItem(LOCAL_AGENT_URL_KEY, input.baseUrl);
  window.localStorage.setItem(LOCAL_AGENT_TOKEN_KEY, input.token);
}

class BankAgentLocalApi {
  async getStatus(input: {
    baseUrl: string;
    token: string;
  }): Promise<LocalAgentStatus> {
    return this.request<LocalAgentStatus>(input, '/status');
  }

  async applyYaml(input: {
    baseUrl: string;
    token: string;
    yaml: string;
  }): Promise<LocalAgentActionResponse> {
    return this.request<LocalAgentActionResponse>(input, '/apply', {
      method: 'POST',
      body: JSON.stringify({ yaml: input.yaml }),
    });
  }

  async signIn(input: {
    baseUrl: string;
    token: string;
    loginId: number;
  }): Promise<LocalAgentActionResponse> {
    return this.request<LocalAgentActionResponse>(
      input,
      `/logins/${input.loginId}/signin`,
      { method: 'POST' }
    );
  }

  async sync(input: {
    baseUrl: string;
    token: string;
    loginId: number;
  }): Promise<LocalAgentActionResponse> {
    return this.request<LocalAgentActionResponse>(
      input,
      `/logins/${input.loginId}/sync`,
      { method: 'POST' }
    );
  }

  private async request<T>(
    input: { baseUrl: string; token: string },
    path: string,
    init: RequestInit = {}
  ): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('Content-Type', 'application/json');
    if (input.token) {
      headers.set('Authorization', `Bearer ${input.token}`);
    }
    const response = await fetch(`${input.baseUrl.replace(/\/$/, '')}${path}`, {
      ...init,
      headers,
    });
    const payload = (await response.json().catch(() => ({}))) as {
      error?: string;
    };
    if (!response.ok) {
      throw new Error(
        payload.error || `Local agent returned ${response.status}`
      );
    }
    return payload as T;
  }
}

export const bankAgentLocalApi = new BankAgentLocalApi();
