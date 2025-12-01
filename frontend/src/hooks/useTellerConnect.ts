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
  user: {
    id: string;
  };
  enrollment: {
    id: string;
    institution: {
      name: string;
    };
  };
  signatures: string[];
  accounts: Array<{
    id: string;
    name: string;
    type: string;
    subtype: string;
    status: string;
  }>;
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
          // Save each account as a separate connection
          for (const account of enrollment.accounts) {
            await tellerApiService.saveTellerConnection({
              access_token: enrollment.accessToken,
              enrollment_id: enrollment.enrollment.id,
              teller_account_id: account.id,
              institution_name: enrollment.enrollment.institution.name,
              account_name: account.name || account.type,
              account_type: account.type,
            });
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
