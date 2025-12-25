import { AccountCreateModal } from '@/components/accounts/AccountCreateModal';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { usePlaidLink } from '@/hooks/usePlaidLink';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import { bankConnectionsApiService } from '@/lib/api/bankConnections';
import { syncService } from '@/lib/api/sync';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import {
  getBankLogo,
  getCardImage,
  getEntityLogo,
  hasSpecificCardImage,
} from '@/lib/imageMapping';
import {
  Building2,
  Cloud,
  CreditCard,
  Landmark,
  Loader2,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { AccountDetailModal } from './AccountDetailModal';
import { DisconnectConfirmModal } from './DisconnectConfirmModal';

interface SyncResult {
  success: boolean;
  accounts_synced: number;
  transactions_synced: number;
  errors: string[];
  message: string;
}

export function UnifiedAccountsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);

  // Modal states
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [showDisconnect, setShowDisconnect] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  // Sync states
  const [syncLoading, setSyncLoading] = useState(false);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Field choices for account creation
  const [accountTypeOptions, setAccountTypeOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [entityOptions, setEntityOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);

  const {
    openPlaidLink,
    loading: plaidLoading,
    error: plaidError,
    clearError: clearPlaidError,
  } = usePlaidLink();

  const { status: syncStatus, refresh: refreshSyncStatus } = useSyncStatus({
    onSyncComplete: () => {
      // Refresh accounts list to show updated data (toast handled globally in Layout)
      refresh();
    },
  });

  // Group accounts by type
  const bankAccounts = accounts.filter(
    acc => acc.account_type === 'checking' || acc.account_type === 'savings'
  );
  const creditCards = accounts.filter(
    acc => acc.account_type === 'credit_card'
  );

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await transactionsApiService.getAccounts();
      setAccounts(data);
      setError(null);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to load accounts';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchFieldChoices = async () => {
    try {
      const choices = await transactionsApiService.getAccountFieldChoices();
      setAccountTypeOptions(choices.type || []);
      setEntityOptions(choices.entity || []);
    } catch (e: unknown) {
      console.error('Failed to load field choices:', e);
      setAccountTypeOptions([
        { value: 'checking', label: 'Checking' },
        { value: 'savings', label: 'Savings' },
        { value: 'credit_card', label: 'Credit Card' },
      ]);
      setEntityOptions([
        { value: 'bank_of_america', label: 'Bank of America' },
        { value: 'chase', label: 'Chase' },
        { value: 'citibank', label: 'Citibank' },
        { value: 'other', label: 'Other' },
      ]);
    }
  };

  useEffect(() => {
    refresh();
    fetchFieldChoices();
  }, []);

  useEffect(() => {
    if (plaidError) {
      setError(plaidError);
      clearPlaidError();
    }
  }, [plaidError, clearPlaidError]);

  // Polling for sync progress
  const pollSyncProgress = useCallback(async (connectionId: number) => {
    try {
      const progress = await bankConnectionsApiService.getSyncJobProgress(connectionId);
      if (progress) {
        if (progress.status !== 'running') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setSyncLoading(false);
          if (progress.status === 'completed') {
            toast.success('Sync completed', {
              description: `Synced ${progress.transactions_synced} transactions`,
            });
          } else if (progress.status === 'failed') {
            toast.error('Sync failed', {
              description: progress.errors?.[0] || 'Unknown error',
            });
          }
          refresh();
        }
      }
    } catch (e) {
      console.error('Error polling sync progress:', e);
    }
  }, []);

  const handleAccountClick = (account: Account) => {
    setSelectedAccount(account);
    setShowDetail(true);
  };

  const handleCreate = async (form: {
    name: string;
    type: string;
    entity: string;
  }) => {
    try {
      setLoading(true);
      await transactionsApiService.createAccount({
        name: form.name,
        type: form.type,
        institution_slug: form.entity,
      });
      await refresh();
      setShowCreate(false);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create account';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (form: {
    name: string;
    type: string;
    entity: string;
    image_key?: string | null;
  }) => {
    if (!selectedAccount) return;
    try {
      setLoading(true);
      await transactionsApiService.updateAccount(selectedAccount.id, {
        name: form.name,
        image_key: form.image_key,
      });
      await refresh();
      setShowDetail(false);
      setSelectedAccount(null);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update account';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedAccount) return;
    try {
      setLoading(true);
      await transactionsApiService.deleteAccount(selectedAccount.id);
      await refresh();
      setShowDetail(false);
      setSelectedAccount(null);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete account';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!selectedAccount?.connection_id) return;

    setSyncLoading(true);
    setShowDetail(false);

    try {
      await bankConnectionsApiService.syncConnection(
        selectedAccount.connection_id
      );
      toast.info('Sync started', {
        description: 'Syncing transactions...',
      });

      // Start polling for progress
      pollIntervalRef.current = setInterval(() => {
        pollSyncProgress(selectedAccount.connection_id!);
      }, 1000);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Sync failed';
      toast.error('Sync failed', {
        description: errorMessage,
      });
      setSyncLoading(false);
    }
  };

  const handleDisconnect = () => {
    setShowDetail(false);
    setShowDisconnect(true);
  };

  const confirmDisconnect = async (deleteData: boolean) => {
    if (!selectedAccount?.connection_id) return;

    try {
      setLoading(true);
      await bankConnectionsApiService.deleteConnection(
        selectedAccount.connection_id,
        deleteData
      );
      await refresh();
      setShowDisconnect(false);
      setSelectedAccount(null);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to disconnect';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectPlaid = () => {
    openPlaidLink(() => {
      refresh();
    });
  };

  const handleSyncAll = async () => {
    try {
      const result = await syncService.triggerSyncAll();
      if (result.status === 'sync_started') {
        toast.info('Sync started', {
          description: 'Syncing all connected accounts...',
        });
        // Refresh sync status to show syncing indicator
        refreshSyncStatus();
      } else if (result.status === 'no_connections') {
        toast.warning('No connected accounts', {
          description: 'Connect a bank account first to sync transactions',
        });
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to start sync';
      toast.error('Sync failed', {
        description: errorMessage,
      });
    }
  };

  // Check if Plaid is available
  const isPlaidAvailable = typeof window !== 'undefined' && !!window.Plaid;
  const isConnecting = plaidLoading;

  // Sync status badge component
  const SyncBadge = ({ account }: { account: Account }) => {
    if (!account.has_connection) return null;

    const statusColors: Record<string, string> = {
      active: 'bg-green-500',
      error: 'bg-red-500',
      disconnected: 'bg-gray-400',
    };

    return (
      <div
        className={`absolute top-2 right-2 z-20 p-1 rounded-full ${statusColors[account.connection_status || 'active']} shadow-md`}
        title={`Synced via Plaid - ${account.connection_status}`}
      >
        <Cloud className="h-3 w-3 text-white" />
      </div>
    );
  };

  // Credit Card visual component (matches CardGrid.tsx CreditCardItem)
  const CreditCardTile = ({ account }: { account: Account }) => {
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const [isHovering, setIsHovering] = useState(false);

    const cardName = account.name;
    const bank = account.entity || '';
    const imageKey = account.image_key;
    const hasSpecificImage = hasSpecificCardImage(cardName, imageKey);
    const cardImage = hasSpecificImage
      ? getCardImage(cardName, bank, imageKey)
      : '/images/credit_cards/default.png';
    const bankLogo = getBankLogo(bank);

    const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      setMousePosition({ x, y });
    };

    return (
      <button
        type="button"
        onClick={() => handleAccountClick(account)}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
        className="rounded-xl relative overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-xl group"
        style={{
          aspectRatio: '1.586',
          width: '100%',
          maxWidth: '220px',
        }}
        aria-label={`Open ${account.name}`}
      >
        {/* Sync Badge */}
        <SyncBadge account={account} />

        {/* Background Image */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `url(${cardImage})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        />

        {/* Glare Effect Overlay */}
        {isHovering && (
          <div
            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
            style={{
              background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 30%, transparent 60%)`,
            }}
          />
        )}

        {/* Dark Overlay for Better Text Readability (only when showing title) */}
        {!hasSpecificImage && (
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
        )}

        {/* Card Content */}
        <div className="absolute inset-0 p-3 flex flex-col justify-between">
          {/* Card Name at Top (only show when using default background) */}
          {!hasSpecificImage && (
            <div className="text-xs font-semibold text-white drop-shadow-lg relative z-10 pr-6">
              {account.name}
            </div>
          )}

          {/* Bank Logo and Last 4 at Bottom */}
          {!hasSpecificImage && (
            <div className="flex justify-between items-end">
              {account.account_number_last4 && (
                <div className="text-xs text-white/80 font-mono drop-shadow-md">
                  ····{account.account_number_last4}
                </div>
              )}
              {bankLogo && (
                <img
                  src={bankLogo}
                  alt={`${bank} logo`}
                  className="w-8 h-8 object-contain drop-shadow-md relative z-10"
                />
              )}
            </div>
          )}
        </div>
      </button>
    );
  };

  // Bank Account visual component with prominent logo
  const BankAccountTile = ({ account }: { account: Account }) => {
    const entity = account.entity || '';
    const entityLogo = getEntityLogo(entity);

    return (
      <button
        type="button"
        onClick={() => handleAccountClick(account)}
        className="rounded-xl border bg-gradient-to-br from-card to-muted/30 p-4 text-left hover:shadow-lg hover:scale-[1.02] transition-all duration-200 relative overflow-hidden group"
        style={{
          minHeight: '100px',
        }}
        aria-label={`Open ${account.name}`}
      >
        {/* Sync Badge */}
        <SyncBadge account={account} />

        {/* Content */}
        <div className="relative z-10 flex flex-col h-full">
          <div className="flex-1">
            <div className="text-sm font-semibold mb-1 truncate pr-8">
              {account.name}
            </div>
            <div className="text-xs text-muted-foreground mb-2">
              {account.institution_name ||
                account.entity_display ||
                'Manual Account'}
            </div>
            {account.account_number_last4 && (
              <div className="text-xs text-muted-foreground font-mono">
                ····{account.account_number_last4}
              </div>
            )}
            {account.account_type_display && (
              <div className="text-xs text-muted-foreground mt-1 capitalize">
                {account.account_type_display}
              </div>
            )}
          </div>

          {/* Bank Logo in bottom-right */}
          {entityLogo && (
            <div className="flex justify-end mt-2">
              <img
                src={entityLogo}
                alt={`${account.institution_name || entity} logo`}
                className="w-8 h-8 object-contain opacity-70 group-hover:opacity-100 transition-opacity"
              />
            </div>
          )}
        </div>
      </button>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Landmark className="h-5 w-5" />
              Accounts
            </CardTitle>
            <CardDescription>
              Manage your bank accounts and credit cards
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {/* Sync All Button */}
            <Button
              type="button"
              variant="outline"
              onClick={handleSyncAll}
              disabled={
                syncStatus?.is_syncing ||
                accounts.filter(a => a.has_connection).length === 0
              }
            >
              {syncStatus?.is_syncing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Sync All
                </>
              )}
            </Button>
            {isPlaidAvailable && (
              <Button
                type="button"
                variant="outline"
                onClick={handleConnectPlaid}
                disabled={isConnecting}
              >
                <Building2 className="h-4 w-4 mr-2" />
                {isConnecting ? 'Connecting...' : 'Connect Bank'}
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCreate(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Manual
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && <div className="text-sm text-red-600 mb-3">{error}</div>}

        {loading && !accounts.length ? (
          <div className="text-sm">Loading...</div>
        ) : accounts.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No accounts yet. Connect a bank or add an account manually.
          </div>
        ) : (
          <>
            {/* Bank Accounts Section */}
            {bankAccounts.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Landmark className="h-4 w-4" />
                  Bank Accounts
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {bankAccounts.map(account => (
                    <BankAccountTile key={account.id} account={account} />
                  ))}
                </div>
              </div>
            )}

            {/* Credit Cards Section */}
            {creditCards.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Credit Cards
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                  {creditCards.map(account => (
                    <CreditCardTile key={account.id} account={account} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>

      {/* Create Modal */}
      <AccountCreateModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={loading}
      />

      {/* Detail/Edit Modal */}
      <AccountDetailModal
        isOpen={showDetail}
        onClose={() => {
          setShowDetail(false);
          setSelectedAccount(null);
        }}
        account={selectedAccount}
        onSubmit={handleUpdate}
        onDelete={handleDelete}
        onSync={handleSync}
        onDisconnect={handleDisconnect}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={loading || syncLoading}
      />

      {/* Disconnect Confirm Modal */}
      <DisconnectConfirmModal
        isOpen={showDisconnect}
        onClose={() => {
          setShowDisconnect(false);
          setSelectedAccount(null);
        }}
        onConfirm={confirmDisconnect}
        loading={loading}
        accountName={selectedAccount?.name}
      />
    </Card>
  );
}
