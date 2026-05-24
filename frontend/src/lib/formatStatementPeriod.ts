export const STATEMENT_PERIOD_MAX_LENGTH = 40;

export function formatSingleMonthPeriod(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}`;
}

function formatIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatStatementPeriodFromRange(from: Date, to: Date): string {
  return `${formatIsoDate(from)} to ${formatIsoDate(to)}`;
}

export function resolveFilingMonth(to: Date): { year: number; month: number } {
  return {
    year: to.getFullYear(),
    month: to.getMonth() + 1,
  };
}

export function validateStatementPeriod(label: string): string | null {
  const trimmed = label.trim();
  if (!trimmed) {
    return 'Statement period label is required';
  }
  if (trimmed.length > STATEMENT_PERIOD_MAX_LENGTH) {
    return `Label must be ${STATEMENT_PERIOD_MAX_LENGTH} characters or fewer`;
  }
  return null;
}

export function statementPeriodDisplayLabel(
  statementPeriod: string,
  statementYear: number,
  statementMonth: number
): string {
  if (statementPeriod.trim()) {
    return statementPeriod;
  }
  return formatSingleMonthPeriod(statementYear, statementMonth);
}
