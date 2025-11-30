/**
 * Image mapping utilities for cards and accounts
 * Maps card names and bank identifiers to their respective image assets
 */

// Mapping of card names (normalized) to specific card images
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
  american_express: '/images/logos/amex.png',
  bank_of_america: '/images/logos/bofa.png',
  chase: '/images/logos/chase.webp',
  citibank: '/images/logos/chase.webp', // Using chase as fallback, could add citi logo
  bilt: '/images/credit_cards/bilt.jpg', // BILT uses specific card image
  other: '', // No default image for other
};

// Mapping of entity identifiers to entity logos
const ENTITY_LOGOS: Record<string, string> = {
  bank_of_america: '/images/logos/bofa.png',
  chase: '/images/logos/chase.webp',
  citibank: '/images/logos/chase.webp', // Using chase as fallback
  marcus: '/images/logos/marcus.png',
  robinhood: '/images/logos/robinhood.png',
  other: '', // No default image for other
};

/**
 * Normalizes a card name for matching against specific card images
 * Converts to lowercase and removes extra whitespace
 */
function normalizeCardName(name: string): string {
  return name.toLowerCase().trim().replace(/\s+/g, ' ');
}

/**
 * Gets the image path for a credit card
 * First tries to match against specific card images by name,
 * then falls back to the bank logo
 *
 * @param cardName - The user-provided name of the card
 * @param bank - The bank identifier (e.g., 'american_express', 'chase')
 * @returns The image path, or empty string if no image is available
 */
export function getCardImage(cardName: string, bank: string): string {
  // First, try to match specific card image by name
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

  // Fall back to bank logo
  return BANK_LOGOS[bank] || '';
}

/**
 * Checks if a card has a specific card image (not just a bank logo)
 *
 * @param cardName - The user-provided name of the card
 * @returns true if a specific card image exists, false otherwise
 */
export function hasSpecificCardImage(cardName: string): boolean {
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
