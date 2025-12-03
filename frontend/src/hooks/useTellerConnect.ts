/**
 * Hook for integrating with Teller Connect
 */
import { tellerApiService } from '@/lib/api/teller';
import { useCallback, useState } from 'react';

// Extend Window interface to include TellerConnect
declare global {
  interface Window {
    TellerConnect: {
      setup: (config: TellerConnectConfig) => TellerConnectInstance;
    };
  }
}

interface TellerConnectConfig {
  applicationId: string;
  environment?: 'sandbox' | 'production';
  onSuccess: (enrollment: TellerEnrollment) => void;
  onExit: () => void;
  onFailure?: (error: any) => void;
}

interface TellerConnectInstance {
  open: () => void;
  destroy: () => void;
}

interface TellerEnrollment {
  accessToken: string;
  user?: {
    id: string;
  };
  enrollment: {
    id: string;
    institution: {
      name: string;
    };
  };
  signatures?: string[];
  accounts?:
    | Array<{
        id: string;
        name?: string;
        type?: string;
        subtype?: string;
        status?: string;
      }>
    | Record<string, any>;
}

export function useTellerConnect() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openTellerConnect = useCallback(async (onSuccess?: () => void) => {
    // Check if Teller Connect SDK is loaded
    if (!window.TellerConnect) {
      setError('Teller Connect SDK not loaded');
      return;
    }

    // Get Teller application ID from environment
    const applicationId = import.meta.env.VITE_TELLER_APP_ID;
    if (!applicationId) {
      setError('Teller Application ID not configured');
      return;
    }

    const tellerConnect = window.TellerConnect.setup({
      applicationId,
      environment: import.meta.env.VITE_TELLER_ENV || 'sandbox',
      onSuccess: async (enrollment: TellerEnrollment) => {
        console.log('Teller enrollment successful:', enrollment);
        setLoading(true);
        setError(null);

        try {
          // The enrollment object structure from Teller
          const accessToken = enrollment.accessToken;
          const enrollmentId = enrollment.enrollment?.id || '';
          const institutionName =
            enrollment.enrollment?.institution?.name || 'Unknown Bank';

          // Accounts might be in different formats - normalize to array
          let accountsArray: Array<{
            id: string;
            name?: string;
            type?: string;
            subtype?: string;
            status?: string;
          }> = [];

          if (enrollment.accounts) {
            if (Array.isArray(enrollment.accounts)) {
              accountsArray = enrollment.accounts;
            } else if (typeof enrollment.accounts === 'object') {
              // If accounts is an object, convert to array
              accountsArray = Object.values(enrollment.accounts);
            }
          }

          console.log('Processing accounts:', accountsArray);

          // If no accounts available from the enrollment response,
          // send enrollment ID and let backend fetch accounts from Teller
          if (accountsArray.length === 0) {
            console.log(
              'No accounts in enrollment response, sending enrollment ID to backend'
            );
            // Backend will detect the enrollment ID and fetch accounts
            await tellerApiService.saveTellerConnection({
              access_token: accessToken,
              enrollment_id: enrollmentId,
              teller_account_id: enrollmentId, // Backend will detect this is an enrollment ID
              institution_name: institutionName,
              account_name: institutionName,
              account_type: 'depository',
            });
          } else {
            // Save each account as a separate connection
            for (const account of accountsArray) {
              await tellerApiService.saveTellerConnection({
                access_token: accessToken,
                enrollment_id: enrollmentId,
                teller_account_id: account.id,
                institution_name: institutionName,
                account_name: account.name || account.type || 'Account',
                account_type: account.type || 'depository',
              });
            }
          }

          if (onSuccess) {
            onSuccess();
          }
        } catch (e: any) {
          console.error('Error saving Teller connection:', e);
          setError(e?.message ?? 'Failed to save connection');
        } finally {
          setLoading(false);
        }
      },
      onExit: () => {
        console.log('Teller Connect closed');
      },
      onFailure: (error: any) => {
        console.error('Teller Connect error:', error);
        setError(error?.message ?? 'Failed to connect');
      },
    });

    // Open Teller Connect
    tellerConnect.open();
  }, []);

  return {
    openTellerConnect,
    loading,
    error,
    clearError: () => setError(null),
  };
}
