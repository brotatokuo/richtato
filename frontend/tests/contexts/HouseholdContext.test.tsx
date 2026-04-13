import { renderHook, waitFor } from '@testing-library/react';
import { type ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import {
  AuthContext,
  type AuthContextType,
} from '@/contexts/AuthContextInstance';
import { HouseholdProvider, useHousehold } from '@/contexts/HouseholdContext';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function makeAuthContext(
  overrides: Partial<AuthContextType> = {}
): AuthContextType {
  return {
    user: {
      id: 1,
      username: 'alice',
      email: 'a@a.com',
    } as AuthContextType['user'],
    organization: null,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    demoLogin: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    ...overrides,
  };
}

function wrapper(authCtx: AuthContextType) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <MemoryRouter>
        <AuthContext.Provider value={authCtx}>
          <HouseholdProvider>{children}</HouseholdProvider>
        </AuthContext.Provider>
      </MemoryRouter>
    );
  };
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('HouseholdContext', () => {
  it('fetches household on mount when authenticated', async () => {
    const mockHousehold = {
      id: 1,
      name: 'Test',
      members: [{ user_id: 1, username: 'alice', joined_at: '2024-01-01' }],
      created_at: '2024-01-01',
    };
    mockFetch.mockResolvedValueOnce(jsonResponse(mockHousehold));

    const { result } = renderHook(() => useHousehold(), {
      wrapper: wrapper(makeAuthContext()),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.household).toBeTruthy();
    expect(result.current.household?.name).toBe('Test');
  });

  it('sets isInHousehold true when household exists', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        id: 1,
        name: 'H',
        members: [{ user_id: 1, username: 'alice', joined_at: '' }],
        created_at: '',
      })
    );

    const { result } = renderHook(() => useHousehold(), {
      wrapper: wrapper(makeAuthContext()),
    });

    await waitFor(() => expect(result.current.isInHousehold).toBe(true));
  });

  it('sets isInHousehold false when no household', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ error: 'Not found' }, 404));

    const { result } = renderHook(() => useHousehold(), {
      wrapper: wrapper(makeAuthContext()),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isInHousehold).toBe(false);
  });

  it('provides partner name from members', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        id: 1,
        name: 'H',
        members: [
          { user_id: 1, username: 'alice', joined_at: '' },
          { user_id: 2, username: 'bob', joined_at: '' },
        ],
        created_at: '',
      })
    );

    const { result } = renderHook(() => useHousehold(), {
      wrapper: wrapper(makeAuthContext()),
    });

    await waitFor(() => expect(result.current.partnerName).toBe('bob'));
  });

  it('does not fetch when not authenticated', async () => {
    const { result } = renderHook(() => useHousehold(), {
      wrapper: wrapper(makeAuthContext({ isAuthenticated: false, user: null })),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockFetch).not.toHaveBeenCalled();
    expect(result.current.isInHousehold).toBe(false);
  });
});
