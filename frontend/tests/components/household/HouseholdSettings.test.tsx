import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {
  HouseholdContext,
  type HouseholdContextType,
  type Scope,
} from '@/contexts/HouseholdContext';
import { HouseholdSettings } from '@/components/household/HouseholdSettings';

const mockCsrfFetch = vi.fn();
vi.mock('@/lib/api/csrf', () => ({
  csrfService: {
    fetchWithCsrf: (...args: unknown[]) => mockCsrfFetch(...args),
    getHeaders: vi.fn().mockResolvedValue({
      'Content-Type': 'application/json',
      'X-CSRFToken': 'fake',
    }),
  },
}));

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function makeCtx(
  overrides: Partial<HouseholdContextType> = {}
): HouseholdContextType {
  return {
    household: null,
    isInHousehold: false,
    isLoading: false,
    scope: 'personal' as Scope,
    setScope: vi.fn(),
    partnerName: null,
    members: [],
    refreshHousehold: vi.fn(),
    ...overrides,
  };
}

function renderWithCtx(ctx: HouseholdContextType) {
  return render(
    <HouseholdContext.Provider value={ctx}>
      <HouseholdSettings />
    </HouseholdContext.Provider>
  );
}

beforeEach(() => {
  mockFetch.mockReset();
  mockCsrfFetch.mockReset();
});

describe('HouseholdSettings - no household', () => {
  it('shows create form when no household', () => {
    renderWithCtx(makeCtx());
    expect(screen.getByPlaceholderText('Household name')).toBeInTheDocument();
    expect(screen.getByText('Create')).toBeInTheDocument();
  });

  it('shows join form with code input', () => {
    renderWithCtx(makeCtx());
    expect(
      screen.getByPlaceholderText('Enter invite code')
    ).toBeInTheDocument();
    expect(screen.getByText('Join')).toBeInTheDocument();
  });

  it('calls create API on submit', async () => {
    mockCsrfFetch.mockResolvedValueOnce(
      jsonResponse({ id: 1, name: 'New', members: [], created_at: '' })
    );
    const refreshHousehold = vi.fn();
    renderWithCtx(makeCtx({ refreshHousehold }));

    fireEvent.change(screen.getByPlaceholderText('Household name'), {
      target: { value: 'Our House' },
    });
    fireEvent.click(screen.getByText('Create'));

    await waitFor(() => expect(refreshHousehold).toHaveBeenCalled());
  });
});

describe('HouseholdSettings - has household', () => {
  const householdCtx = makeCtx({
    household: {
      id: 1,
      name: 'The Smiths',
      members: [
        { user_id: 1, username: 'alice', joined_at: '2024-01-01T00:00:00Z' },
      ],
      created_at: '2024-01-01',
    },
    isInHousehold: true,
    members: [
      { user_id: 1, username: 'alice', joined_at: '2024-01-01T00:00:00Z' },
    ],
  });

  it('shows household name and members', () => {
    renderWithCtx(householdCtx);
    expect(screen.getByText('The Smiths')).toBeInTheDocument();
    expect(screen.getByText('alice')).toBeInTheDocument();
  });

  it('shows generate invite button when less than 2 members', () => {
    renderWithCtx(householdCtx);
    expect(screen.getByText('Generate Invite Code')).toBeInTheDocument();
  });

  it('shows invite code after generating', async () => {
    mockCsrfFetch.mockResolvedValueOnce(
      jsonResponse({
        invite_code: 'TEST1234',
        expires_at: '2024-01-03T00:00:00Z',
      })
    );
    renderWithCtx(householdCtx);
    fireEvent.click(screen.getByText('Generate Invite Code'));

    await waitFor(() => {
      expect(screen.getByText('TEST1234')).toBeInTheDocument();
    });
  });

  it('has leave household button', () => {
    renderWithCtx(householdCtx);
    expect(screen.getByText('Leave Household')).toBeInTheDocument();
  });
});

describe('HouseholdSettings - join flow', () => {
  it('calls join API with entered code', async () => {
    mockCsrfFetch.mockResolvedValueOnce(
      jsonResponse({ id: 1, name: 'Joined', members: [], created_at: '' })
    );
    const refreshHousehold = vi.fn();
    renderWithCtx(makeCtx({ refreshHousehold }));

    fireEvent.change(screen.getByPlaceholderText('Enter invite code'), {
      target: { value: 'ABC12345' },
    });
    fireEvent.click(screen.getByText('Join'));

    await waitFor(() => expect(refreshHousehold).toHaveBeenCalled());
  });
});
