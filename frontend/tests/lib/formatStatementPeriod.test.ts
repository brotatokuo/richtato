import {
  formatSingleMonthPeriod,
  formatStatementPeriodFromRange,
  parseIsoDateString,
  resolveFilingMonth,
  statementPeriodDisplayLabel,
  validateCustomDateRange,
  validateStatementPeriod,
} from '@/lib/formatStatementPeriod';

describe('formatStatementPeriod', () => {
  it('formats a single month period', () => {
    expect(formatSingleMonthPeriod(2025, 6)).toBe('2025-06');
  });

  it('formats a compact custom range label', () => {
    const from = new Date(2025, 9, 15);
    const to = new Date(2026, 0, 14);

    expect(formatStatementPeriodFromRange(from, to)).toBe(
      '2025-10-15 to 2026-01-14'
    );
    expect(formatStatementPeriodFromRange(from, to).length).toBeLessThanOrEqual(
      40
    );
  });

  it('resolves filing month from the range end date', () => {
    const to = new Date(2026, 0, 14);

    expect(resolveFilingMonth(to)).toEqual({ year: 2026, month: 1 });
  });

  it('validates statement period length', () => {
    expect(validateStatementPeriod('')).toBe(
      'Statement period label is required'
    );
    expect(validateStatementPeriod('2025-06')).toBeNull();
    expect(validateStatementPeriod('a'.repeat(41))).toBe(
      'Label must be 40 characters or fewer'
    );
  });

  it('prefers stored statement period for display', () => {
    expect(
      statementPeriodDisplayLabel('2025-10-15 to 2026-01-14', 2026, 1)
    ).toBe('2025-10-15 to 2026-01-14');
    expect(statementPeriodDisplayLabel('', 2025, 6)).toBe('2025-06');
  });

  it('parses ISO date strings', () => {
    expect(parseIsoDateString('2026-01-14')).toEqual(new Date(2026, 0, 14));
    expect(parseIsoDateString('')).toBeNull();
    expect(parseIsoDateString('2026-13-01')).toBeNull();
    expect(parseIsoDateString('not-a-date')).toBeNull();
  });

  it('validates custom date ranges', () => {
    expect(validateCustomDateRange('', '2026-01-14')).toBe(
      'Start and end dates are required'
    );
    expect(validateCustomDateRange('2026-01-14', '2026-01-01')).toBe(
      'Start date must be on or before end date'
    );
    expect(validateCustomDateRange('2025-10-15', '2026-01-14')).toBeNull();
  });
});
