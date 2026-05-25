import { screen } from '@testing-library/react';
import { BankSyncSection } from '@/components/settings/BankSyncSection';
import { bankSyncApi } from '@/lib/api/bankSync';
import { render as renderWithRouter } from '../../test-utils/utils';

vi.mock('@/lib/api/bankSync', () => ({
  bankSyncApi: {
    getSetup: vi.fn(),
    updateSyncMode: vi.fn(),
    getApiToken: vi.fn(),
  },
  SYNC_MODE_OPTIONS: [
    { value: 'auto', label: 'Auto sync', description: 'Agent' },
    { value: 'upload', label: 'Statement upload', description: 'Upload' },
    { value: 'manual', label: 'Manual entry', description: 'Manual' },
  ],
  agentFlowLabel: (flow: string | null) =>
    flow === 'investment_balance' ? 'Portfolio balance scrape' : 'Not supported',
}));

const mockGetSetup = vi.mocked(bankSyncApi.getSetup);

beforeEach(() => {
  mockGetSetup.mockReset();
});

describe('BankSyncSection', () => {
  it('renders account sync details from the setup API', async () => {
    mockGetSetup.mockResolvedValue({
      accounts: [
        {
          id: 1,
          name: 'Robinhood Brokerage',
          institution_slug: 'robinhood',
          institution_name: 'Robinhood',
          account_type: 'investment',
          account_type_display: 'Investment Account',
          sync_mode: 'manual',
          agent_sync_supported: true,
          agent_flow: 'investment_balance',
          needs_storage_for_auto: false,
          has_storage_uri: false,
          resolved_storage_uri: '',
        },
      ],
      agent_config: {
        version: 1,
        generated_at: '2026-01-01T00:00:00Z',
        user_id: 1,
        source: 'richtato_accounts',
        logins: [],
      },
    });

    renderWithRouter(<BankSyncSection />);

    expect(await screen.findByText('Robinhood Brokerage')).toBeInTheDocument();
    expect(screen.getByText(/Portfolio balance scrape/)).toBeInTheDocument();
    expect(screen.getByText(/Host Agent Setup/)).toBeInTheDocument();
    expect(screen.getByText(/Host Agent Credentials/)).toBeInTheDocument();
    expect(screen.getAllByText(/BANK_AGENT_FERNET_KEY/).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Download .env/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /sync mode for robinhood brokerage/i })).toBeInTheDocument();
  });
});
