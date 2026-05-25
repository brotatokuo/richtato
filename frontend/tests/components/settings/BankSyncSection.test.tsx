import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BankSyncSection } from '@/components/settings/BankSyncSection';
import { bankSyncApi } from '@/lib/api/bankSync';
import { render as renderWithRouter } from '../../test-utils/utils';

vi.mock('@/lib/api/bankSync', () => ({
  bankSyncApi: {
    getSetup: vi.fn(),
    updateSyncMode: vi.fn(),
    updateAccountSchedule: vi.fn(),
    updateActivityUrl: vi.fn(),
    downloadSetupYaml: vi.fn(),
  },
  SYNC_MODE_OPTIONS: [
    { value: 'auto', label: 'Auto sync', description: 'Agent' },
    { value: 'upload', label: 'Statement upload', description: 'Upload' },
    { value: 'manual', label: 'Manual entry', description: 'Manual' },
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
const mockUpdateActivityUrl = vi.mocked(bankSyncApi.updateActivityUrl);

beforeEach(() => {
  mockGetSetup.mockReset();
  mockDownloadSetupYaml.mockReset();
  mockUpdateActivityUrl.mockReset();
});

describe('BankSyncSection', () => {
  it('renders account sync details, schedule controls, and download setup', async () => {
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
    expect(screen.getByText(/richtato bank setup/)).toBeInTheDocument();
    expect(
      screen.getByRole('combobox', {
        name: /sync mode for robinhood brokerage/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('combobox', {
        name: /sync cadence for robinhood brokerage/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('combobox', {
        name: /sync hour for robinhood brokerage/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /download setup/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('textbox', {
        name: /activity url for robinhood brokerage/i,
      })
    ).toBeInTheDocument();
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

  it('saves activity url edits when the field loses focus', async () => {
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
    mockUpdateActivityUrl.mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderWithRouter(<BankSyncSection />);

    const input = await screen.findByRole('textbox', {
      name: /activity url for bofa personal/i,
    });
    await user.type(input, 'https://secure.bankofamerica.com/activity?adx=abc');
    await user.tab();

    expect(mockUpdateActivityUrl).toHaveBeenCalledWith(
      3,
      'https://secure.bankofamerica.com/activity?adx=abc'
    );
    expect(screen.getByText(/On demand/)).toBeInTheDocument();
  });
});
