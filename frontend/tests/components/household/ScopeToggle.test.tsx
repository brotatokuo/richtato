import { render, screen, fireEvent } from '@testing-library/react';
import {
  HouseholdContext,
  type HouseholdContextType,
  type Scope,
} from '@/contexts/HouseholdContext';
import { ScopeToggle } from '@/components/household/ScopeToggle';

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
      <ScopeToggle />
    </HouseholdContext.Provider>
  );
}

describe('ScopeToggle', () => {
  it('renders personal and household options when in household', () => {
    renderWithCtx(makeCtx({ isInHousehold: true }));
    expect(screen.getByText('Personal')).toBeInTheDocument();
    expect(screen.getByText('Household')).toBeInTheDocument();
  });

  it('defaults to personal scope', () => {
    const ctx = makeCtx({ isInHousehold: true, scope: 'personal' });
    renderWithCtx(ctx);
    // Personal button should have the active styling (bg-background class)
    const personalBtn = screen.getByText('Personal').closest('button');
    expect(personalBtn?.className).toContain('bg-background');
  });

  it('calls setScope on click', () => {
    const setScope = vi.fn();
    const ctx = makeCtx({ isInHousehold: true, setScope });
    renderWithCtx(ctx);
    fireEvent.click(screen.getByText('Household'));
    expect(setScope).toHaveBeenCalledWith('household');
  });

  it('renders nothing when not in household', () => {
    const { container } = renderWithCtx(makeCtx({ isInHousehold: false }));
    expect(container.innerHTML).toBe('');
  });
});
