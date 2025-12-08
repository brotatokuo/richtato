/**
 * Teller API service for bank connections
 *
 * @deprecated Use bankConnectionsApiService from '@/lib/api/bankConnections' instead.
 * This file is kept for backwards compatibility.
 */

// Re-export everything from bankConnections
export {
  bankConnectionsApiService as tellerApiService,
  type BankConnection as TellerConnection,
  type CreateConnectionInput as CreateTellerConnectionInput,
  type CreateConnectionResponse as CreateTellerConnectionResponse,
  type SyncResult as TellerSyncResult,
  type SyncJobProgress,
} from './bankConnections';
