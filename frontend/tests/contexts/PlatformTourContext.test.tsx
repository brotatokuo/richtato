import { PlatformTourProvider } from '@/contexts/PlatformTourContext';
import { PreferencesProvider } from '@/contexts/PreferencesContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { username: 'demo' },
  }),
}));

const preferencesApi = vi.hoisted(() => ({
  get: vi.fn(),
  update: vi.fn(),
  getFieldChoices: vi.fn(),
}));

vi.mock('@/lib/api/user', async importOriginal => {
  const actual = await importOriginal<typeof import('@/lib/api/user')>();
  return {
    ...actual,
    preferencesApi,
  };
});

vi.mock('react-joyride', () => ({
  Joyride: ({ run }: { run?: boolean }) =>
    run ? <div data-testid="joyride-tour">Tour running</div> : null,
  ACTIONS: {},
  EVENTS: {},
  STATUS: {},
}));

function renderTourProvider(initialPath = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <PreferencesProvider>
          <PlatformTourProvider>
            <div>App shell</div>
          </PlatformTourProvider>
        </PreferencesProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('PlatformTourProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    preferencesApi.get.mockResolvedValue({
      theme: 'system',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      timezone: 'UTC',
      platform_tour_completed: false,
    });
    preferencesApi.getFieldChoices.mockResolvedValue({
      theme: [],
      date_format: [],
      currency: [{ value: 'USD', label: 'USD ($)' }],
      timezone: [],
    });
    preferencesApi.update.mockResolvedValue({
      theme: 'system',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      timezone: 'UTC',
      platform_tour_completed: true,
    });
  });

  it('auto-starts the tour for first-login users', async () => {
    renderTourProvider();

    await waitFor(() => {
      expect(screen.getByTestId('joyride-tour')).toBeInTheDocument();
    });
  });

  it('does not auto-start when the tour is already completed', async () => {
    preferencesApi.get.mockResolvedValue({
      theme: 'system',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      timezone: 'UTC',
      platform_tour_completed: true,
    });

    renderTourProvider();

    await waitFor(() => {
      expect(preferencesApi.get).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByTestId('joyride-tour')).not.toBeInTheDocument();
    });
  });
});
