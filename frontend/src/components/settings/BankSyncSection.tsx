import { ConnectBankDialog } from '@/components/bank-automation/ConnectBankDialog';
import { ConnectionCard } from '@/components/bank-automation/ConnectionCard';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  bankAutomationApi,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { Building2, ChromeIcon, Plus, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

/**
 * Bank Sync (Chrome-extension automation) panel for the Setup → Accounts page.
 *
 * Mirrors the standalone /bank-automation page, but lives next to the user's
 * manual + Plaid-connected accounts so the whole "where do my balances come
 * from" story is in one place.
 */
export function BankSyncSection() {
  const [connections, setConnections] = useState<BankAutomationConnection[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectOpen, setConnectOpen] = useState(false);

  const refresh = async () => {
    try {
      setError(null);
      const list = await bankAutomationApi.listConnections();
      setConnections(list);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load bank-sync connections'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const handleConnectionChange = (next: BankAutomationConnection) => {
    setConnections(prev =>
      prev.some(c => c.id === next.id)
        ? prev.map(c => (c.id === next.id ? next : c))
        : [next, ...prev]
    );
  };

  const handleConnectionRemoved = (id: number) => {
    setConnections(prev => prev.filter(c => c.id !== id));
  };

  const handleConnected = (connection: BankAutomationConnection) => {
    handleConnectionChange(connection);
    toast.success(`${connection.institution_name} connected`);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Bank Sync
            </CardTitle>
            <CardDescription>
              Let Richtato fetch CSV statements on a schedule using a session
              captured by the Richtato Chrome extension. Your bank password and
              MFA never leave your browser.
            </CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            onClick={() => setConnectOpen(true)}
            className="shrink-0 gap-2"
          >
            <Plus className="h-4 w-4" />
            Connect bank
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start gap-3 rounded-md border border-dashed border-border bg-muted/30 p-3 text-sm text-muted-foreground">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <p>
            Add the bank accounts you want synced under <em>Accounts</em> above
            first. Then sign in to your bank in Chrome, click the Richtato
            extension, and tick the matching Richtato accounts.
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : connections.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-8 text-center">
            <ChromeIcon className="h-9 w-9 text-muted-foreground" />
            <div className="space-y-1">
              <p className="text-sm font-medium">
                No bank-sync connections yet
              </p>
              <p className="max-w-md text-xs text-muted-foreground">
                Install the extension, log in to your bank as you normally
                would, then click &ldquo;Connect bank&rdquo; to capture an
                authenticated session.
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              onClick={() => setConnectOpen(true)}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Connect bank
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {connections.map(connection => (
              <ConnectionCard
                key={connection.id}
                connection={connection}
                onChange={handleConnectionChange}
                onRemoved={handleConnectionRemoved}
              />
            ))}
          </div>
        )}
      </CardContent>

      <ConnectBankDialog
        open={connectOpen}
        onOpenChange={setConnectOpen}
        onConnected={handleConnected}
        initialConnectionIds={connections.map(c => c.id)}
      />
    </Card>
  );
}
