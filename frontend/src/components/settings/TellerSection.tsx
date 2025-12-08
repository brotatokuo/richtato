/**
 * TellerSection - Re-exports BankConnectionsSection for backwards compatibility.
 *
 * This component is deprecated. Use BankConnectionsSection instead which
 * supports both Teller and Plaid connections.
 */
export {
  BankConnectionsSection,
  BankConnectionsSection as TellerSection,
} from './BankConnectionsSection';
