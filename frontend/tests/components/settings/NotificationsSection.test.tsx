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

it('renders the master notification switch and saves toggles', async () => {
  mockGet.mockResolvedValue({
    notifications_enabled: true,
  });
  mockUpdate.mockResolvedValue({});

  const user = userEvent.setup();
  render(<NotificationsSection />);

  await user.click(
    await screen.findByRole('switch', { name: /Enable notifications/i })
  );

  expect(mockUpdate).toHaveBeenCalledWith({
    notifications_enabled: false,
  });
});
