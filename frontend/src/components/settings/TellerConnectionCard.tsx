import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { TellerConnection } from '@/lib/api/teller';
import { Building2, RefreshCw } from 'lucide-react';

interface TellerConnectionCardProps {
  connection: TellerConnection;
  onSync: (connection: TellerConnection) => void;
  onDisconnect: (connection: TellerConnection) => void;
}

export function TellerConnectionCard({
  connection,
  onSync,
  onDisconnect,
}: TellerConnectionCardProps) {
  const statusColors = {
    active: 'text-green-600',
    disconnected: 'text-gray-500',
    error: 'text-red-600',
  };

  const lastSyncDate = connection.last_sync
    ? new Date(connection.last_sync).toLocaleDateString()
    : 'Never';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-base">
                {connection.institution_name}
              </CardTitle>
              <CardDescription className="text-sm">
                {connection.account_name}
              </CardDescription>
            </div>
          </div>
          <span
            className={`text-xs font-medium ${statusColors[connection.status]}`}
          >
            {connection.status_display || connection.status}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-xs text-muted-foreground">
          Provider: {connection.provider_display || connection.provider}
        </div>
        <div className="text-xs text-muted-foreground">
          Last synced: {lastSyncDate}
        </div>
        {connection.last_sync_error && (
          <div className="text-xs text-red-600">
            Error: {connection.last_sync_error}
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onSync(connection)}
            disabled={connection.status === 'disconnected'}
            className="flex-1"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Sync
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onDisconnect(connection)}
            disabled={connection.status === 'disconnected'}
            className="flex-1"
          >
            Disconnect
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
