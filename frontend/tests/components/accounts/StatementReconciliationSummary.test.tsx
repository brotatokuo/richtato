import { StatementReconciliationSummary } from '@/components/accounts/StatementReconciliationSummary';
import { render, screen } from '@testing-library/react';

describe('StatementReconciliationSummary', () => {
  it('shows neutral preview copy when opening balances differ', () => {
    render(
      <StatementReconciliationSummary
        result={{
          balance_summary: {
            beginning_balance: '1617.51',
            ending_balance: '1555.33',
            beginning_date: '2024-11-25',
            ending_date: '2024-11-25',
          },
          reconciliation: {
            opening_balance_action: 'available_update',
            statement_beginning_balance: '1617.51',
            account_opening_balance_current: '723.98',
          },
          reconciliation_warnings: [],
        }}
      />
    );

    expect(
      screen.getByText(/differs from account opening balance/i)
    ).toBeInTheDocument();
    expect(screen.queryByText(/will be set/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/will be updated/i)).not.toBeInTheDocument();
  });

  it('shows matched copy when opening balances align', () => {
    render(
      <StatementReconciliationSummary
        result={{
          balance_summary: {
            beginning_balance: '723.98',
            ending_balance: '450.72',
          },
          reconciliation: {
            opening_balance_action: 'matched',
          },
          reconciliation_warnings: [],
        }}
      />
    );

    expect(
      screen.getByText(/matches statement beginning balance/i)
    ).toBeInTheDocument();
  });
});
