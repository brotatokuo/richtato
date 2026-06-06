/**
 * Image mapping utilities for account institution logos.
 */

// Mapping of bank identifiers to bank logos
const BANK_LOGOS: Record<string, string> = {
  // Major Banks
  chase: '/images/logos/chase.webp',
  bank_of_america: '/images/logos/bofa.png',
  wells_fargo: '/images/logos/wells_fargo.png',
  citibank: '/images/logos/citi.webp',
  capital_one: '',
  us_bank: '',
  pnc: '',
  td_bank: '',
  // Online Banks
  ally: '',
  discover: '',
  sofi: '/images/logos/sofi.png',
  // Credit Card Issuers
  american_express: '/images/logos/amex.png',
  bilt: '',
  // Investment / Brokerage
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  schwab: '/images/logos/charles_schwab.png',
  fidelity: '/images/logos/fidelity.png',
  guideline: '/images/logos/guideline.png',
  vanguard: '',
  // Credit Unions
  navy_federal: '',
  // Other
  other: '',
};

/**
 * Gets the bank logo path
 *
 * @param bank - The bank identifier (e.g., 'american_express', 'chase')
 * @returns The bank logo path, or empty string if no logo is available
 */
export function getBankLogo(bank: string): string {
  return BANK_LOGOS[bank] || '';
}

/**
 * Gets the logo path for an entity (account)
 *
 * @param entity - The entity identifier (e.g., 'bank_of_america', 'marcus')
 * @returns The logo path, or empty string if no logo is available
 */
export function getEntityLogo(entity: string): string {
  return BANK_LOGOS[entity] || '';
}
