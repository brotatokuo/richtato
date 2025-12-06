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
  { key: 'amex_blue_cash', label: 'Amex Blue Cash', path: '/images/credit_cards/amex_blue_cash.avif' },
  { key: 'amex_platinum', label: 'Amex Platinum', path: '/images/credit_cards/amex_platinum.avif' },
  { key: 'amex_delta_platinum', label: 'Amex Delta Platinum', path: '/images/credit_cards/amex_delta_platinum.avif' },
  { key: 'bilt', label: 'Bilt', path: '/images/credit_cards/bilt.jpg' },
  { key: 'bofa_custom_cash', label: 'BofA Custom Cash', path: '/images/credit_cards/bofa_custom_cash.png' },
  { key: 'citi_costco', label: 'Citi Costco', path: '/images/credit_cards/citi_costco.jpg' },
  { key: 'citi_custom_cash', label: 'Citi Custom Cash', path: '/images/credit_cards/citi_custom_cash.png' },
];

// Mapping from image key to path (for quick lookup)
const CARD_IMAGE_BY_KEY: Record<string, string> = Object.fromEntries(
  AVAILABLE_CARD_IMAGES.map(img => [img.key, img.path])
);

// Mapping of card names (normalized) to specific card images (for auto-detection)
const SPECIFIC_CARD_IMAGES: Record<string, string> = {
  'amex blue cash': '/images/credit_cards/amex_blue_cash.avif',
  'amex platinum': '/images/credit_cards/amex_platinum.avif',
  'amex delta platinum': '/images/credit_cards/amex_delta_platinum.avif',
  bilt: '/images/credit_cards/bilt.jpg',
  'bofa custom cash': '/images/credit_cards/bofa_custom_cash.png',
  'bank of america custom cash': '/images/credit_cards/bofa_custom_cash.png',
  'citi costco': '/images/credit_cards/citi_costco.jpg',
  'citi custom cash': '/images/credit_cards/citi_custom_cash.png',
};

// Mapping of bank identifiers to bank logos
const BANK_LOGOS: Record<string, string> = {
  // Major Banks
  chase: '/images/logos/chase.webp',
  bank_of_america: '/images/logos/bofa.png',
  wells_fargo: '',
  citibank: '',
  capital_one: '',
  us_bank: '',
  pnc: '',
  td_bank: '',
  // Online Banks
  ally: '',
  discover: '',
  sofi: '',
  // Credit Card Issuers
  american_express: '/images/logos/amex.png',
  bilt: '/images/credit_cards/bilt.jpg',
  // Investment / Brokerage
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  schwab: '',
  fidelity: '',
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
  wells_fargo: '',
  citibank: '',
  capital_one: '',
  us_bank: '',
  pnc: '',
  td_bank: '',
  // Online Banks
  ally: '',
  discover: '',
  sofi: '',
  // Credit Card Issuers
  american_express: '/images/logos/amex.png',
  // Investment / Brokerage
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  schwab: '',
  fidelity: '',
  vanguard: '',
  // Credit Unions
  navy_federal: '',
  // Other
  other: '',
};

/**
 * Normalizes a card name for matching against specific card images
 * Converts to lowercase and removes extra whitespace
 */
function normalizeCardName(name: string): string {
  return name.toLowerCase().trim().replace(/\s+/g, ' ');
}

/**
 * Gets the image path for a credit card.
 * Priority: 1) Manual image_key override, 2) Auto-detect from card name, 3) Bank logo fallback
 *
 * @param cardName - The user-provided name of the card
 * @param bank - The bank identifier (e.g., 'american_express', 'chase')
 * @param imageKey - Optional manual image key override (from database)
 * @returns The image path, or empty string if no image is available
 */
export function getCardImage(cardName: string, bank: string, imageKey?: string | null): string {
  // Priority 1: Use manual image_key override if provided
  if (imageKey && CARD_IMAGE_BY_KEY[imageKey]) {
    return CARD_IMAGE_BY_KEY[imageKey];
  }

  // Priority 2: Try to auto-detect from card name
  const normalizedName = normalizeCardName(cardName);

  // Check for exact match
  if (SPECIFIC_CARD_IMAGES[normalizedName]) {
    return SPECIFIC_CARD_IMAGES[normalizedName];
  }

  // Check for partial matches (e.g., "My Amex Blue Cash" should match "amex blue cash")
  for (const [key, imagePath] of Object.entries(SPECIFIC_CARD_IMAGES)) {
    if (normalizedName.includes(key) || key.includes(normalizedName)) {
      return imagePath;
    }
  }

  // Priority 3: Fall back to bank logo
  return BANK_LOGOS[bank] || '';
}

/**
 * Checks if a card has a specific card image (not just a bank logo)
 *
 * @param cardName - The user-provided name of the card
 * @param imageKey - Optional manual image key override
 * @returns true if a specific card image exists, false otherwise
 */
export function hasSpecificCardImage(cardName: string, imageKey?: string | null): boolean {
  // Check manual override first
  if (imageKey && CARD_IMAGE_BY_KEY[imageKey]) {
    return true;
  }

  const normalizedName = normalizeCardName(cardName);

  // Check for exact match
  if (SPECIFIC_CARD_IMAGES[normalizedName]) {
    return true;
  }

  // Check for partial matches
  for (const key of Object.keys(SPECIFIC_CARD_IMAGES)) {
    if (normalizedName.includes(key) || key.includes(normalizedName)) {
      return true;
    }
  }

  return false;
}

/**
 * Gets the auto-detected image key from a card name (if any)
 * Used to show which image would be auto-detected in the picker
 *
 * @param cardName - The user-provided name of the card
 * @returns The image key if auto-detected, undefined otherwise
 */
export function getAutoDetectedImageKey(cardName: string): string | undefined {
  const normalizedName = normalizeCardName(cardName);

  // Check for exact match first
  for (const img of AVAILABLE_CARD_IMAGES) {
    const searchKey = img.label.toLowerCase().replace(/\s+/g, ' ');
    if (normalizedName === searchKey) {
      return img.key;
    }
  }

  // Check for partial matches
  for (const img of AVAILABLE_CARD_IMAGES) {
    const searchKey = img.label.toLowerCase().replace(/\s+/g, ' ');
    if (normalizedName.includes(searchKey) || searchKey.includes(normalizedName)) {
      return img.key;
    }
  }

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
