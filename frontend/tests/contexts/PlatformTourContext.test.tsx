import { PlatformTourProvider, usePlatformTour } from '@/contexts/PlatformTourContext';
import { PreferencesProvider } from '@/contexts/PreferencesContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { cleanupJoyridePortal } from '@/lib/tour/platformTourEvents';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  ACTIONS: { NEXT: 'next', PREV: 'prev', CLOSE: 'close', SKIP: 'skip' },
  EVENTS: {
    STEP_AFTER: 'step:after',
    TARGET_NOT_FOUND: 'error:target_not_found',
    TOUR_END: 'tour:end',
  },
  STATUS: {
    RUNNING: 'running',
    FINISHED: 'finished',
    SKIPPED: 'skipped',
  },
}));

function ReplayButton() {
  const { startTour, isRunning } = usePlatformTour();
  return (
    <button type="button" disabled={isRunning} onClick={() => startTour(0)}>
      Replay tour
    </button>
  );
}

function renderTourProvider(initialPath = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <PreferencesProvider>
          <PlatformTourProvider>
            <ReplayButton />
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

  it('can replay the tour after it was completed', async () => {
    preferencesApi.get.mockResolvedValue({
      theme: 'system',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      timezone: 'UTC',
      platform_tour_completed: true,
    });

    const user = userEvent.setup();
    renderTourProvider('/preferences');

    await waitFor(() => {
      expect(preferencesApi.get).toHaveBeenCalled();
    });

    await user.click(screen.getByRole('button', { name: 'Replay tour' }));

    await waitFor(() => {
      expect(screen.getByTestId('joyride-tour')).toBeInTheDocument();
    });

    cleanupJoyridePortal();
  });
});
