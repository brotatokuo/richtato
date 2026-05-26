import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BankSyncSection } from '@/components/settings/BankSyncSection';
import { bankAgentLocalApi } from '@/lib/api/bankAgentLocal';
import { bankSyncApi } from '@/lib/api/bankSync';
import { render as renderWithRouter } from '../../test-utils/utils';

vi.mock('@/lib/api/bankAgentLocal', () => ({
  bankAgentLocalApi: {
    getStatus: vi.fn(),
    applyYaml: vi.fn(),
    signIn: vi.fn(),
    sync: vi.fn(),
  },
  getStoredLocalAgentConnection: () => ({
    baseUrl: 'http://127.0.0.1:8765',
    token: '',
  }),
  storeLocalAgentConnection: vi.fn(),
}));

vi.mock('@/lib/api/bankSync', () => ({
  bankSyncApi: {
    getSetup: vi.fn(),
    updateSyncMode: vi.fn(),
    updateAccountSchedule: vi.fn(),
    updateActivityUrl: vi.fn(),
    getSetupYamlText: vi.fn(),
    downloadSetupYaml: vi.fn(),
  },
  SYNC_MODE_OPTIONS: [
    { value: 'auto', label: 'Automatic import', description: 'Agent' },
    { value: 'upload', label: 'Statement uploads', description: 'Upload' },
    { value: 'manual', label: 'Manual tracking', description: 'Manual' },
  ],
  AGENT_CADENCE_OPTIONS: [
    { value: 'manual', label: 'On demand' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
  ],
  AGENT_HOUR_OPTIONS: [{ value: 6, label: '06:00' }],
  agentFlowLabel: (flow: string | null) =>
    flow === 'investment_balance'
      ? 'Portfolio balance scrape'
      : 'Not supported',
}));

const mockGetSetup = vi.mocked(bankSyncApi.getSetup);
const mockDownloadSetupYaml = vi.mocked(bankSyncApi.downloadSetupYaml);
const mockGetLocalStatus = vi.mocked(bankAgentLocalApi.getStatus);

beforeEach(() => {
  cleanup();
  mockGetSetup.mockReset();
  mockDownloadSetupYaml.mockReset();
  mockGetLocalStatus.mockReset();
});

describe('BankSyncSection', () => {
  it('renders read-only account setup status and download setup', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [
        {
          id: 1,
          name: 'Robinhood Brokerage',
          institution_slug: 'robinhood',
          institution_name: 'Robinhood',
          account_type: 'investment',
          account_type_display: 'Investment Account',
          sync_mode: 'auto',
          agent_cadence: 'daily',
          agent_sync_hour: 6,
          agent_sync_supported: true,
          agent_flow: 'investment_balance',
          needs_storage_for_auto: false,
          has_storage_uri: false,
          resolved_storage_uri: '',
          activity_url: '',
          has_activity_url: false,
          needs_activity_url_for_auto: true,
        },
      ],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [
          {
            institution: 'robinhood',
            nickname: 'personal',
            cadence: 'daily',
            hour: 6,
            accounts: [],
          },
        ],
      },
      duplicate_institution_logins: [],
    });

    renderWithRouter(<BankSyncSection />);

    expect(await screen.findByText('Robinhood Brokerage')).toBeInTheDocument();
    expect(screen.getByText(/Portfolio balance scrape/)).toBeInTheDocument();
    expect(screen.getByText(/Host Agent Setup/)).toBeInTheDocument();
    expect(screen.getByText(/Local Agent Connection/)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /cli commands/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /edit setup/i })).toHaveAttribute(
      'href',
      '/accounts'
    );
    expect(
      screen.getByRole('button', { name: /download setup/i })
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Activity URL/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/needs an activity URL/i)).toBeInTheDocument();
  });

  it('downloads setup yaml when the button is clicked', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [
        {
          id: 2,
          name: 'Chase Checking',
          institution_slug: 'chase',
          institution_name: 'Chase',
          account_type: 'checking',
          account_type_display: 'Checking Account',
          sync_mode: 'auto',
          agent_cadence: 'daily',
          agent_sync_hour: 6,
          agent_sync_supported: true,
          agent_flow: 'deposit',
          needs_storage_for_auto: true,
          has_storage_uri: true,
          resolved_storage_uri: 'gdrive://folder',
          activity_url: 'https://secure.chase.com/activity?accountId=abc',
          has_activity_url: true,
          needs_activity_url_for_auto: false,
        },
      ],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [
          {
            institution: 'chase',
            nickname: 'personal',
            cadence: 'daily',
            hour: 6,
            accounts: [
              {
                name: 'Chase Checking',
                flow: 'deposit',
                storage_uri: 'gdrive://folder',
                richtato_account_id: 2,
                activity_url: 'https://secure.chase.com/activity?accountId=abc',
              },
            ],
          },
        ],
      },
      duplicate_institution_logins: [],
    });
    mockDownloadSetupYaml.mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderWithRouter(<BankSyncSection />);

    await screen.findByText('Chase Checking');
    await user.click(screen.getByRole('button', { name: /download setup/i }));

    expect(mockDownloadSetupYaml).toHaveBeenCalledTimes(1);
  });

  it('loads local bank-agent status', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [],
      },
      duplicate_institution_logins: [],
    });
    mockGetLocalStatus.mockResolvedValue({
      ok: true,
      reauth_required: true,
      login_count: 1,
      account_count: 1,
      logins: [
        {
          id: 4,
          institution_slug: 'bofa',
          nickname: 'personal',
          status: 'needs_reauth',
          cadence: 'daily',
          preferred_run_hour_local: 6,
          next_run_at: null,
          last_run_at: null,
          last_success_at: null,
          last_failure_kind: 'needs_reauth',
          last_failure_reason: 'Redirected to sign-in',
          cookies_captured_at: null,
          accounts: [],
        },
      ],
      recent_runs: [],
    });

    const user = userEvent.setup();
    renderWithRouter(<BankSyncSection />);

    await screen.findByText(/No linked accounts yet/i);
    await user.click(screen.getByRole('button', { name: /connect/i }));

    expect(mockGetLocalStatus).toHaveBeenCalled();
  });

  it('shows logged-in state when local agent reports an active session', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [],
      },
      duplicate_institution_logins: [],
    });
    mockGetLocalStatus.mockResolvedValue({
      ok: true,
      reauth_required: false,
      login_count: 1,
      account_count: 1,
      logins: [
        {
          id: 5,
          institution_slug: 'chase',
          nickname: 'personal',
          status: 'active',
          cadence: 'daily',
          preferred_run_hour_local: 6,
          next_run_at: '2026-05-26T06:00:00Z',
          last_run_at: '2026-05-25T06:00:00Z',
          last_success_at: '2026-05-25T06:00:00Z',
          last_failure_kind: null,
          last_failure_reason: '',
          cookies_captured_at: '2026-05-24T12:00:00Z',
          accounts: [],
        },
      ],
      recent_runs: [],
    });

    const user = userEvent.setup();
    renderWithRouter(<BankSyncSection />);

    await screen.findByText(/No linked accounts yet/i);
    await user.click(screen.getByRole('button', { name: /connect/i }));

    expect(mockGetLocalStatus).toHaveBeenCalled();
  });

  it('shows missing activity url status as account setup guidance', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [
        {
          id: 3,
          name: 'BofA Personal',
          institution_slug: 'bofa',
          institution_name: 'Bank of America',
          account_type: 'checking',
          account_type_display: 'Checking Account',
          sync_mode: 'auto',
          agent_cadence: 'manual',
          agent_sync_hour: 6,
          agent_sync_supported: true,
          agent_flow: 'deposit',
          needs_storage_for_auto: true,
          has_storage_uri: true,
          resolved_storage_uri: 'gdrive://folder',
          activity_url: '',
          has_activity_url: false,
          needs_activity_url_for_auto: true,
        },
      ],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [
          {
            institution: 'bofa',
            nickname: 'personal',
            cadence: 'manual',
            hour: 6,
            accounts: [],
          },
        ],
      },
      duplicate_institution_logins: [],
    });
    renderWithRouter(<BankSyncSection />);

    expect(await screen.findByText('BofA Personal')).toBeInTheDocument();
    expect(screen.getAllByText(/Activity URL/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Missing/i)).toBeInTheDocument();
    expect(
      screen.getByText(/edit flow before applying setup/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText(/On demand/).length).toBeGreaterThan(0);
  });
});
