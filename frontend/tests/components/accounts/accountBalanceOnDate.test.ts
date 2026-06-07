import { canSetBalanceOnDate } from '@/components/accounts/accountBalanceOnDate';

describe('canSetBalanceOnDate', () => {
  it('allows checking, savings, and investment accounts', () => {
    expect(canSetBalanceOnDate({ account_type: 'checking' })).toBe(true);
    expect(canSetBalanceOnDate({ account_type: 'savings' })).toBe(true);
    expect(canSetBalanceOnDate({ account_type: 'investment' })).toBe(true);
  });

  it('blocks credit card accounts', () => {
    expect(canSetBalanceOnDate({ account_type: 'credit_card' })).toBe(false);
  });

  it('respects balance_snapshots sync capability', () => {
    expect(
      canSetBalanceOnDate({
        account_type: 'checking',
        sync_capabilities: { balance_snapshots: false },
      })
    ).toBe(false);
  });

  it('falls back to type when account_type is missing', () => {
    expect(canSetBalanceOnDate({ type: 'savings' })).toBe(true);
  });
});
