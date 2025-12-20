/**
 * Image mapping utilities for cards and accounts
 * Maps card names and bank identifiers to their respective image assets
 */

/**
 * Available card images that users can choose from.
 * Each entry has a unique key used for storage and a path to the image.
 */
export interface CardImageOption {
  key: string;
  label: string;
  path: string;
}

export const AVAILABLE_CARD_IMAGES: CardImageOption[] = [
  {
    key: 'amex_blue_cash',
    label: 'Amex Blue Cash',
    path: '/images/credit_cards/amex_blue_cash.avif',
  },
  {
    key: 'amex_gold',
    label: 'Amex Gold',
    path: '/images/credit_cards/amex_gold.png',
  },
  {
    key: 'amex_platinum',
    label: 'Amex Platinum',
    path: '/images/credit_cards/amex_platinum.avif',
  },
  {
    key: 'amex_delta_platinum',
    label: 'Amex Delta Platinum',
    path: '/images/credit_cards/amex_delta_platinum.avif',
  },
  { key: 'bilt', label: 'Bilt', path: '/images/credit_cards/bilt.jpg' },
  {
    key: 'bofa_custom_cash',
    label: 'BofA Custom Cash',
    path: '/images/credit_cards/bofa_custom_cash.png',
  },
  {
    key: 'citi_costco',
    label: 'Citi Costco',
    path: '/images/credit_cards/citi_costco.jpg',
  },
  {
    key: 'citi_custom_cash',
    label: 'Citi Custom Cash',
    path: '/images/credit_cards/citi_custom_cash.png',
  },
  {
    key: 'chase_sapphire_preferred',
    label: 'Chase Sapphire Preferred',
    path: '/images/credit_cards/chase_sapphire_preferred.png',
  },
  {
    key: 'chase_sapphire_reserve',
    label: 'Chase Sapphire Reserve',
    path: '/images/credit_cards/chase_sapphire_reserve.png',
  },
  {
    key: 'venturex',
    label: 'Capital One Venture X',
    path: '/images/credit_cards/venturex.avif',
  },
];

// Mapping from image key to path (for quick lookup)
const CARD_IMAGE_BY_KEY: Record<string, string> = Object.fromEntries(
  AVAILABLE_CARD_IMAGES.map(img => [img.key, img.path])
);

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
  bilt: '/images/credit_cards/bilt.jpg',
  // Investment / Brokerage
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  schwab: '/images/logos/charles_schwab.png',
  fidelity: '/images/logos/fidelity.png',
  vanguard: '',
  // Credit Unions
  navy_federal: '',
  // Other
  other: '',
};

// Mapping of entity identifiers to entity logos (same as bank logos for consistency)
const ENTITY_LOGOS: Record<string, string> = {
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
  // Investment / Brokerage
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  schwab: '/images/logos/charles_schwab.png',
  fidelity: '/images/logos/fidelity.png',
  vanguard: '',
  // Credit Unions
  navy_federal: '',
  // Other
  other: '',
};

/**
 * Gets the image path for a credit card.
 * Priority: 1) Manual image_key override, 2) Bank logo fallback
 *
 * @param _cardName - The user-provided name of the card (unused, kept for API compatibility)
 * @param bank - The bank identifier (e.g., 'american_express', 'chase')
 * @param imageKey - Optional manual image key override (from database)
 * @returns The image path, or empty string if no image is available
 */
export function getCardImage(
  _cardName: string,
  bank: string,
  imageKey?: string | null
): string {
  // Priority 1: Use manual image_key override if provided
  if (imageKey && CARD_IMAGE_BY_KEY[imageKey]) {
    return CARD_IMAGE_BY_KEY[imageKey];
  }

  // Priority 2: Fall back to bank logo
  return BANK_LOGOS[bank] || '';
}

/**
 * Checks if a card has a specific card image (not just a bank logo)
 *
 * @param _cardName - The user-provided name of the card (unused, kept for API compatibility)
 * @param imageKey - Optional manual image key override
 * @returns true if a specific card image exists, false otherwise
 */
export function hasSpecificCardImage(
  _cardName: string,
  imageKey?: string | null
): boolean {
  // Only check manual override - no auto-detection
  return !!(imageKey && CARD_IMAGE_BY_KEY[imageKey]);
}

/**
 * Gets the auto-detected image key from a card name (if any)
 * Auto-detection is disabled - always returns undefined.
 * Kept for API compatibility with components that use it.
 *
 * @param _cardName - The user-provided name of the card (unused)
 * @returns Always undefined (auto-detection disabled)
 */
export function getAutoDetectedImageKey(_cardName: string): string | undefined {
  // Auto-detection is disabled - images must be explicitly set via image_key
  return undefined;
}

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
  return ENTITY_LOGOS[entity] || '';
}
