import { screen, waitFor } from '@testing-library/react';
import { AccountSyncSettings } from '@/components/accounts/AccountSyncSettings';
import { render } from '../../test-utils/utils';

const institutions = [
  {
    value: 'chase',
    label: 'Chase',
    account_types: [{ value: 'checking', label: 'Checking Account' }],
    agent_flows: [
      {
        account_type: 'checking',
        flow: 'deposit' as const,
        needs_storage: true,
      },
    ],
  },
];

describe('AccountSyncSettings', () => {
  it('explains automatic import and Drive requirements for supported accounts', () => {
    render(
      <AccountSyncSettings
        form={{
          entity: 'chase',
          type: 'checking',
          syncMode: 'auto',
          agentCadence: 'daily',
          agentSyncHour: 6,
          agentActivityUrl: '',
        }}
        institutions={institutions}
        hasStorageUri={false}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByText('Automatic import')).toBeInTheDocument();
    expect(screen.getByText('Statement download')).toBeInTheDocument();
    expect(
      screen.getByText(/needs a Google Drive statement folder/i)
    ).toBeInTheDocument();
  });

  it('falls back to manual tracking when automatic import is unsupported', async () => {
    const onChange = vi.fn();
    render(
      <AccountSyncSettings
        form={{
          entity: 'other',
          type: 'checking',
          syncMode: 'auto',
          agentCadence: 'daily',
          agentSyncHour: 6,
          agentActivityUrl: '',
        }}
        institutions={institutions}
        onChange={onChange}
      />
    );

    expect(
      screen.getByText(/Automatic import is not available/i)
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(onChange).toHaveBeenCalledWith('syncMode', 'manual')
    );
  });
});
