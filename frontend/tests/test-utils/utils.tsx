/* eslint-disable react-refresh/only-export-components -- test helpers export render wrapper */
import { render, type RenderOptions } from '@testing-library/react';
import { type ReactElement, type ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { BudgetDateRangeProvider } from '@/contexts/BudgetDateRangeContext';
import {
  AuthContext,
  type AuthContextType,
} from '@/contexts/AuthContextInstance';

const mockAuthContext: AuthContextType = {
  user: {
    id: 1,
    username: 'testuser',
    email: 'test@test.com',
  } as AuthContextType['user'],
  organization: null,
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  demoLogin: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
};

function AllProviders({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <AuthContext.Provider value={mockAuthContext}>
        <BudgetDateRangeProvider>{children}</BudgetDateRangeProvider>
      </AuthContext.Provider>
    </MemoryRouter>
  );
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export { customRender as render };
