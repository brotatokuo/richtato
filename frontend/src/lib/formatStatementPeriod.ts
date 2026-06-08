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

export function parseIsoDateString(value: string): Date | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(year, month - 1, day);
  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    return null;
  }
  return parsed;
}

export function validateCustomDateRange(
  start: string,
  end: string
): string | null {
  if (!start.trim() || !end.trim()) {
    return 'Start and end dates are required';
  }
  const startDate = parseIsoDateString(start);
  const endDate = parseIsoDateString(end);
  if (!startDate || !endDate) {
    return 'Enter valid dates in YYYY-MM-DD format';
  }
  if (startDate > endDate) {
    return 'Start date must be on or before end date';
  }
  const label = formatStatementPeriodFromRange(startDate, endDate);
  if (label.length > STATEMENT_PERIOD_MAX_LENGTH) {
    return `Date range label must be ${STATEMENT_PERIOD_MAX_LENGTH} characters or fewer`;
  }
  return null;
}

export function resolveFilingMonth(to: Date): { year: number; month: number } {
  return {
    year: to.getFullYear(),
    month: to.getMonth() + 1,
  };
}

export function isPastStatementMonth(
  year: number,
  month: number,
  reference: Date = new Date()
): boolean {
  const referenceYear = reference.getFullYear();
  const referenceMonth = reference.getMonth() + 1;

  if (year !== referenceYear) {
    return year < referenceYear;
  }

  return month < referenceMonth;
}

export function resolveStatementStatusForMonth(
  year: number,
  month: number,
  reference: Date = new Date()
): 'provisional' | 'closed' {
  return isPastStatementMonth(year, month, reference)
    ? 'closed'
    : 'provisional';
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
