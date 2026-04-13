/**
 * Formatting utilities for currency and dates based on user preferences
 */

// Currency symbols mapping
export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  NTD: 'NT$',
  EUR: '€',
  GBP: '£',
  CAD: 'C$',
  AUD: 'A$',
  JPY: '¥',
  CNY: '¥',
  INR: '₹',
};

/**
 * Get the currency symbol for a given currency code
 */
export function getCurrencySymbol(currency: string = 'USD'): string {
  return CURRENCY_SYMBOLS[currency] || '$';
}

/**
 * Format a number as currency based on user preferences
 */
export function formatCurrency(
  amount: number | string,
  currency: string = 'USD',
  decimals: number = 2
): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(numAmount)) {
    return `${CURRENCY_SYMBOLS[currency] || '$'}0.00`;
  }

  const symbol = CURRENCY_SYMBOLS[currency] || '$';
  const absAmount = Math.abs(numAmount);
  const formattedAmount = absAmount.toFixed(decimals);

  // Add thousand separators
  const parts = formattedAmount.split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  return `${symbol}${parts.join('.')}`;
}

/**
 * Format a date string or Date object based on user preference
 */
export function formatDate(
  date: string | Date | null | undefined,
  format: string = 'MM/DD/YYYY'
): string {
  if (!date) return '';

  let dateObj: Date;
  if (typeof date === 'string') {
    // Handle ISO date strings (YYYY-MM-DD)
    const [year, month, day] = date.split('-').map(Number);
    // Create date in local timezone without UTC shift
    dateObj = new Date(year, (month ?? 1) - 1, day ?? 1);
  } else {
    dateObj = date;
  }

  if (isNaN(dateObj.getTime())) {
    return '';
  }

  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');

  switch (format) {
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`;
    case 'DD/MM/YYYY':
      return `${day}/${month}/${year}`;
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    default:
      return `${month}/${day}/${year}`;
  }
}

/**
 * Format a currency amount with sign (for income/expenses)
 */
export function formatSignedCurrency(
  amount: number | string,
  currency: string = 'USD',
  showPositiveSign: boolean = false
): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(numAmount)) {
    return formatCurrency(0, currency);
  }

  const sign = numAmount >= 0 ? (showPositiveSign ? '+' : '') : '-';

  return `${sign}${formatCurrency(Math.abs(numAmount), currency)}`;
}

const PERIOD_LABELS: Record<string, string> = {
  '30d': '30d',
  '60d': '60d',
  '90d': '90d',
  '6m': '6mo',
  '1y': '1yr',
};

export function formatPeriodLabel(period: string): string {
  return PERIOD_LABELS[period] ?? period;
}
