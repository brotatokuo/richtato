import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationsSection } from '@/components/settings/NotificationsSection';
import { preferencesApi } from '@/lib/api/user';
import { render } from '../../test-utils/utils';

vi.mock('@/lib/api/user', () => ({
  preferencesApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
}));

const mockGet = vi.mocked(preferencesApi.get);
const mockUpdate = vi.mocked(preferencesApi.update);

beforeEach(() => {
  mockGet.mockReset();
  mockUpdate.mockReset();
});

it('renders bank sync notification preferences and saves email opt in', async () => {
  mockGet.mockResolvedValue({
    notifications_enabled: true,
    bank_sync_in_app_notifications: true,
    bank_sync_email_notifications: false,
    bank_sync_daily_digest: true,
  });
  mockUpdate.mockResolvedValue({});

  const user = userEvent.setup();
  render(<NotificationsSection />);

  expect((await screen.findAllByText(/Bank sync/i)).length).toBeGreaterThan(0);
  await user.click(
    screen.getByRole('switch', { name: /Immediate email alerts/i })
  );

  expect(mockUpdate).toHaveBeenCalledWith({
    bank_sync_email_notifications: true,
  });
});
