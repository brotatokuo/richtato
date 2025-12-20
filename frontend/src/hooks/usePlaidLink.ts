/**
 * Hook for integrating with Plaid Link
 */
import { bankConnectionsApiService } from '@/lib/api/bankConnections';
import { useCallback, useState } from 'react';

// Extend Window interface to include Plaid
declare global {
  interface Window {
    Plaid: {
      create: (config: PlaidLinkConfig) => PlaidLinkInstance;
    };
  }
}

interface PlaidLinkConfig {
  token: string;
  onSuccess: (publicToken: string, metadata: PlaidLinkMetadata) => void;
  onExit: (err: PlaidLinkError | null, metadata: PlaidLinkMetadata) => void;
  onEvent?: (eventName: string, metadata: PlaidLinkEventMetadata) => void;
  onLoad?: () => void;
}

interface PlaidLinkInstance {
  open: () => void;
  exit: (options?: { force?: boolean }) => void;
  destroy: () => void;
}

interface PlaidLinkMetadata {
  link_session_id: string;
  institution: {
    name: string;
    institution_id: string;
  } | null;
  accounts: Array<{
    id: string;
    name: string;
    mask: string;
    type: string;
    subtype: string;
  }>;
  account?: {
    id: string;
    name: string;
    mask: string;
    type: string;
    subtype: string;
  };
  account_id?: string;
  transfer_status?: string;
}

interface PlaidLinkError {
  error_type: string;
  error_code: string;
  error_message: string;
  display_message: string | null;
}

interface PlaidLinkEventMetadata {
  error_type?: string;
  error_code?: string;
  error_message?: string;
  exit_status?: string;
  institution_id?: string;
  institution_name?: string;
  institution_search_query?: string;
  link_session_id?: string;
  mfa_type?: string;
  request_id?: string;
  view_name?: string;
  timestamp?: string;
}

export function usePlaidLink() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkToken, setLinkToken] = useState<string | null>(null);

  const openPlaidLink = useCallback(async (onSuccess?: () => void) => {
    // Check if Plaid SDK is loaded
    if (!window.Plaid) {
      setError('Plaid Link SDK not loaded');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Get link token from backend
      const token = await bankConnectionsApiService.createPlaidLinkToken();
      setLinkToken(token);

      // Create Plaid Link handler
      const plaidLink = window.Plaid.create({
        token,
        onSuccess: async (publicToken: string, metadata: PlaidLinkMetadata) => {
          setLoading(true);
          setError(null);

          try {
            const institutionName =
              metadata.institution?.name || 'Unknown Bank';

            // Exchange public token for access token and create connections
            await bankConnectionsApiService.exchangePlaidToken(
              publicToken,
              institutionName
            );

            if (onSuccess) {
              onSuccess();
            }
          } catch (e: any) {
            console.error('Error saving Plaid connection:', e);
            setError(e?.message ?? 'Failed to save connection');
          } finally {
            setLoading(false);
          }
        },
        onExit: (err: PlaidLinkError | null) => {
          setLoading(false);

          if (err) {
            setError(err.display_message || err.error_message || 'Connection failed');
          }
        },
        onLoad: () => {
          setLoading(false);
        },
      });

      // Open Plaid Link
      plaidLink.open();
    } catch (e: any) {
      console.error('Error initializing Plaid Link:', e);
      setError(e?.message ?? 'Failed to initialize Plaid Link');
      setLoading(false);
    }
  }, []);

  return {
    openPlaidLink,
    loading,
    error,
    linkToken,
    clearError: () => setError(null),
  };
}
