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
        setLoading(true);
        setError(null);

        try {
          // Extract enrollment data - backend will fetch all accounts from Teller
          const accessToken = enrollment.accessToken;
          const enrollmentId = enrollment.enrollment?.id || '';
          const institutionName =
            enrollment.enrollment?.institution?.name || 'Unknown Bank';

          // Send enrollment ID to backend - it will fetch all accounts from Teller
          // and create a FinancialAccount + SyncConnection for each
          await tellerApiService.saveTellerConnection({
            access_token: accessToken,
            external_enrollment_id: enrollmentId,
            institution_name: institutionName,
          });

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
        // Connection dialog closed
      },
      onFailure: (error: any) => {
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
