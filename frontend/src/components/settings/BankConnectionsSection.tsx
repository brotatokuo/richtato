import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { usePlaidLink } from '@/hooks/usePlaidLink';
import {
  BankConnection,
  bankConnectionsApiService,
} from '@/lib/api/bankConnections';
import { Building2, Cloud, Plus, RefreshCw, Unlink } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { DisconnectConfirmModal } from './DisconnectConfirmModal';

export function BankConnectionsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connections, setConnections] = useState<BankConnection[]>([]);

  const [showDisconnect, setShowDisconnect] = useState(false);
  const [selectedConnection, setSelectedConnection] =
    useState<BankConnection | null>(null);

  const [syncAllLoading, setSyncAllLoading] = useState(false);

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
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to load bank connections';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (plaidError) {
      setError(plaidError);
      clearPlaidError();
    }
  }, [plaidError, clearPlaidError]);

  const handleConnectPlaid = () => {
    openPlaidLink(refresh);
  };

  const handleSync = async (
    connection: BankConnection,
    fullSync: boolean = false
  ) => {
    try {
      toast.info('Sync started', {
        description: `Syncing ${connection.institution_name}...`,
      });
      const result = await bankConnectionsApiService.syncConnection(
        connection.id,
        fullSync
      );
      if (result.success) {
        toast.success('Sync completed', {
          description: `Synced ${result.transactions_synced} transactions`,
        });
      } else {
        toast.error('Sync failed', {
          description: result.errors?.[0] || 'Unknown error',
        });
      }
      await refresh();
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to sync connection';
      toast.error('Sync failed', {
        description: errorMessage,
      });
    }
  };

  const handleDisconnect = (connection: BankConnection) => {
    setSelectedConnection(connection);
    setShowDisconnect(true);
  };

  const confirmDisconnect = async (deleteData: boolean) => {
    if (!selectedConnection) return;

    try {
      setLoading(true);
      await bankConnectionsApiService.deleteConnection(selectedConnection.id, deleteData);
      await refresh();
      setShowDisconnect(false);
      setSelectedConnection(null);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to disconnect';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncAll = async () => {
    const activeConnections = connections.filter(c => c.status === 'active');

    if (activeConnections.length === 0) {
      setError('No active connections to sync');
      return;
    }

    setSyncAllLoading(true);

    try {
      let totalTransactionsSynced = 0;
      const allErrors: string[] = [];

      // Sync each connection sequentially
      for (const connection of activeConnections) {
        try {
          const result = await bankConnectionsApiService.syncConnection(
            connection.id,
            false // incremental sync
          );
          totalTransactionsSynced += result.transactions_synced;
          allErrors.push(...result.errors);
        } catch (e: unknown) {
          const errorMessage = e instanceof Error ? e.message : 'Failed to sync';
          allErrors.push(
            `${connection.institution_name}: ${errorMessage}`
          );
        }
      }

      if (allErrors.length === 0) {
        toast.success('Sync completed', {
          description: `Synced ${totalTransactionsSynced} transactions from ${activeConnections.length} connection(s)`,
        });
      } else {
        toast.warning('Sync completed with errors', {
          description: `${allErrors.length} error(s) occurred`,
        });
      }

      // Refresh connections to update last_sync times
      await refresh();
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to sync connections';
      toast.error('Sync failed', {
        description: errorMessage,
      });
    } finally {
      setSyncAllLoading(false);
    }
  };

  const isConnecting = plaidLoading;

  // Check if Plaid is available
  const isPlaidAvailable = typeof window !== 'undefined' && !!window.Plaid;

  const formatLastSync = (lastSync: string | null) => {
    if (!lastSync) return 'Never';
    try {
      const date = new Date(lastSync);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };

  const statusColors: Record<string, string> = {
    active: 'text-green-600',
    error: 'text-red-600',
    disconnected: 'text-gray-500',
  };

  const statusBgColors: Record<string, string> = {
    active: 'bg-green-500',
    error: 'bg-red-500',
    disconnected: 'bg-gray-400',
  };

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
              Connect and sync your bank accounts via Plaid
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
            {isPlaidAvailable && (
              <Button
                type="button"
                variant="outline"
                onClick={handleConnectPlaid}
                disabled={isConnecting || loading}
              >
                <Plus className="h-4 w-4 mr-2" />
                {isConnecting ? 'Connecting...' : 'Connect Bank'}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
        {loading && !connections.length ? (
          <div className="py-4 flex justify-center"><LoadingSpinner /></div>
        ) : connections.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No bank connections yet. Click "Connect Bank" to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {connections.map(connection => (
              <div
                key={connection.id}
                className="rounded-lg border bg-card p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{connection.institution_name}</div>
                    <div className="text-sm text-muted-foreground">
                      {connection.account_name}
                    </div>
                  </div>
                  <div
                    className={`p-1.5 rounded-full ${statusBgColors[connection.status]}`}
                    title={`Status: ${connection.status}`}
                  >
                    <Cloud className="h-3 w-3 text-white" />
                  </div>
                </div>

                <div className="text-xs text-muted-foreground">
                  <span className={statusColors[connection.status]}>
                    {connection.status_display}
                  </span>
                  {' • '}
                  Last sync: {formatLastSync(connection.last_sync)}
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSync(connection)}
                    disabled={loading || connection.status === 'disconnected'}
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Sync
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDisconnect(connection)}
                    disabled={loading}
                    className="text-orange-600 hover:text-orange-700"
                  >
                    <Unlink className="h-3 w-3 mr-1" />
                    Disconnect
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <DisconnectConfirmModal
        isOpen={showDisconnect}
        onClose={() => setShowDisconnect(false)}
        onConfirm={confirmDisconnect}
        loading={loading}
        accountName={selectedConnection?.institution_name}
      />
    </Card>
  );
}
