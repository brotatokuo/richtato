import { ConnectBankDialog } from '@/components/bank-automation/ConnectBankDialog';
import { ConnectionCard } from '@/components/bank-automation/ConnectionCard';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  bankAutomationApi,
  type BankAutomationConnection,
} from '@/lib/api/bankAutomation';
import { ChromeIcon, Plus, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

export function BankAutomation() {
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
        err instanceof Error ? err.message : 'Failed to load connections'
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
    <div className="space-y-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">
            Bank Automation
          </h2>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Let Richtato fetch CSV statements on your schedule. Sessions come
            from the Richtato Chrome extension, so your bank password and MFA
            stay with you.
          </p>
        </div>
        <Button
          onClick={() => setConnectOpen(true)}
          className="gap-2 self-start md:self-auto"
        >
          <Plus className="h-4 w-4" />
          Connect bank
        </Button>
      </header>

      <Card className="border-dashed">
        <CardContent className="flex items-start gap-3 p-4">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div className="text-sm text-muted-foreground">
            <p className="font-medium text-foreground">How this works</p>
            <p>
              You sign in to your bank in Chrome with your password manager and
              any MFA. The Richtato extension reads the resulting session
              cookies (never the password) and posts an encrypted blob to
              Richtato. Our headless runner reuses those cookies once per
              cadence to download CSVs and import them automatically.
            </p>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : connections.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
            <ChromeIcon className="h-10 w-10 text-muted-foreground" />
            <div className="space-y-1">
              <p className="text-base font-medium">No bank connections yet</p>
              <p className="max-w-md text-sm text-muted-foreground">
                Install the Chrome extension, log in to your bank as you
                normally would, then click "Connect bank" to capture an
                authenticated session.
              </p>
            </div>
            <Button onClick={() => setConnectOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Connect bank
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
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

      <ConnectBankDialog
        open={connectOpen}
        onOpenChange={setConnectOpen}
        onConnected={handleConnected}
        initialConnectionIds={connections.map(c => c.id)}
      />
    </div>
  );
}
