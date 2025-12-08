import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePlaidLink } from '@/hooks/usePlaidLink';
import { useTellerConnect } from '@/hooks/useTellerConnect';
import {
  BankConnection,
  SyncResult,
  bankConnectionsApiService,
} from '@/lib/api/bankConnections';
import { Building2, ChevronDown, Plus, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { TellerConnectionCard } from './TellerConnectionCard';
import { TellerDisconnectModal } from './TellerDisconnectModal';
import { TellerSyncModal } from './TellerSyncModal';

export function BankConnectionsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connections, setConnections] = useState<BankConnection[]>([]);

  const [showDisconnect, setShowDisconnect] = useState(false);
  const [showSync, setShowSync] = useState(false);
  const [selectedConnection, setSelectedConnection] =
    useState<BankConnection | null>(null);

  const [syncLoading, setSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncAllLoading, setSyncAllLoading] = useState(false);

  // Teller Connect hook
  const {
    openTellerConnect,
    loading: tellerLoading,
    error: tellerError,
    clearError: clearTellerError,
  } = useTellerConnect();

  // Plaid Link hook
  const {
    openPlaidLink,
    loading: plaidLoading,
    error: plaidError,
    clearError: clearPlaidError,
  } = usePlaidLink();

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await bankConnectionsApiService.getConnections();
      setConnections(data);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load bank connections');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (tellerError) {
      setError(tellerError);
      clearTellerError();
    }
  }, [tellerError, clearTellerError]);

  useEffect(() => {
    if (plaidError) {
      setError(plaidError);
      clearPlaidError();
    }
  }, [plaidError, clearPlaidError]);

  const handleConnectTeller = () => {
    openTellerConnect(refresh);
  };

  const handleConnectPlaid = () => {
    openPlaidLink(refresh);
  };

  const handleSync = async (
    connection: BankConnection,
    fullSync: boolean = false
  ) => {
    setSelectedConnection(connection);
    setShowSync(true);
    setSyncLoading(true);
    setSyncResult(null);

    try {
      const result = await bankConnectionsApiService.syncConnection(
        connection.id,
        fullSync
      );
      setSyncResult(result);
      await refresh();
    } catch (e: any) {
      setSyncResult({
        success: false,
        accounts_synced: 0,
        transactions_synced: 0,
        errors: [e?.message ?? 'Failed to sync connection'],
        message: 'Sync failed',
      });
    } finally {
      setSyncLoading(false);
    }
  };

  const handleDisconnect = (connection: BankConnection) => {
    setSelectedConnection(connection);
    setShowDisconnect(true);
  };

  const confirmDisconnect = async () => {
    if (!selectedConnection) return;

    try {
      setLoading(true);
      await bankConnectionsApiService.deleteConnection(selectedConnection.id);
      await refresh();
      setShowDisconnect(false);
      setSelectedConnection(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to disconnect');
    } finally {
      setLoading(false);
    }
  };

  const closeSync = () => {
    setShowSync(false);
    setSyncResult(null);
    setSelectedConnection(null);
  };

  const handleSyncAll = async () => {
    const activeConnections = connections.filter(c => c.status === 'active');

    if (activeConnections.length === 0) {
      setError('No active connections to sync');
      return;
    }

    setSyncAllLoading(true);
    setShowSync(true);
    setSyncLoading(true);
    setSyncResult(null);

    try {
      let totalAccountsSynced = 0;
      let totalTransactionsSynced = 0;
      const allErrors: string[] = [];

      // Sync each connection sequentially
      for (const connection of activeConnections) {
        try {
          const result = await bankConnectionsApiService.syncConnection(
            connection.id,
            false // incremental sync
          );
          totalAccountsSynced += result.accounts_synced;
          totalTransactionsSynced += result.transactions_synced;
          allErrors.push(...result.errors);
        } catch (e: any) {
          allErrors.push(
            `${connection.institution_name}: ${e?.message ?? 'Failed to sync'}`
          );
        }
      }

      setSyncResult({
        success: allErrors.length === 0,
        accounts_synced: totalAccountsSynced,
        transactions_synced: totalTransactionsSynced,
        errors: allErrors,
        message:
          allErrors.length === 0
            ? `Successfully synced ${activeConnections.length} connection(s)`
            : `Synced with ${allErrors.length} error(s)`,
      });

      // Refresh connections to update last_sync times
      await refresh();
    } catch (e: any) {
      setSyncResult({
        success: false,
        accounts_synced: 0,
        transactions_synced: 0,
        errors: [e?.message ?? 'Failed to sync connections'],
        message: 'Sync failed',
      });
    } finally {
      setSyncLoading(false);
      setSyncAllLoading(false);
    }
  };

  const isConnecting = tellerLoading || plaidLoading;

  // Check which providers are available
  const isTellerAvailable =
    typeof window !== 'undefined' &&
    !!window.TellerConnect &&
    !!import.meta.env.VITE_TELLER_APP_ID;
  const isPlaidAvailable = typeof window !== 'undefined' && !!window.Plaid;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Bank Connections
            </CardTitle>
            <CardDescription>
              Connect and sync your bank accounts via Teller or Plaid
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {connections.length > 0 && (
              <Button
                type="button"
                variant="outline"
                onClick={handleSyncAll}
                disabled={
                  syncAllLoading ||
                  loading ||
                  connections.filter(c => c.status === 'active').length === 0
                }
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${syncAllLoading ? 'animate-spin' : ''}`}
                />
                {syncAllLoading ? 'Syncing...' : 'Sync All'}
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  disabled={isConnecting || loading}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  {isConnecting ? 'Connecting...' : 'Connect Bank'}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {isTellerAvailable && (
                  <DropdownMenuItem onClick={handleConnectTeller}>
                    <span className="mr-2">🏦</span>
                    Connect via Teller
                  </DropdownMenuItem>
                )}
                {isPlaidAvailable && (
                  <DropdownMenuItem onClick={handleConnectPlaid}>
                    <span className="mr-2">💳</span>
                    Connect via Plaid
                  </DropdownMenuItem>
                )}
                {!isTellerAvailable && !isPlaidAvailable && (
                  <DropdownMenuItem disabled>
                    No providers configured
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
        {loading && !connections.length ? (
          <div className="text-sm">Loading...</div>
        ) : connections.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No bank connections yet. Click "Connect Bank" to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {connections.map(connection => (
              <TellerConnectionCard
                key={connection.id}
                connection={connection}
                onSync={handleSync}
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        )}
      </CardContent>

      <TellerDisconnectModal
        isOpen={showDisconnect}
        onClose={() => setShowDisconnect(false)}
        onConfirm={confirmDisconnect}
        loading={loading}
        institutionName={selectedConnection?.institution_name}
      />

      <TellerSyncModal
        isOpen={showSync}
        onClose={closeSync}
        loading={syncLoading}
        result={syncResult}
      />
    </Card>
  );
}

// Export the old name for backwards compatibility
export { BankConnectionsSection as TellerSection };
