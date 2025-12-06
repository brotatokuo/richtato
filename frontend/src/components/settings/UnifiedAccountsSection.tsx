import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useTellerConnect } from '@/hooks/useTellerConnect';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import {
  SyncJobProgress,
  TellerSyncResult,
  tellerApiService,
} from '@/lib/api/teller';
import {
  Building2,
  Cloud,
  CreditCard,
  Landmark,
  Plus,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { AccountCreateModal } from '@/components/accounts/AccountCreateModal';
import { AccountDetailModal } from './AccountDetailModal';
import { DisconnectConfirmModal } from './DisconnectConfirmModal';
import { TellerSyncModal } from './TellerSyncModal';

export function UnifiedAccountsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);

  // Modal states
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [showDisconnect, setShowDisconnect] = useState(false);
  const [showSync, setShowSync] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  // Sync states
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<TellerSyncResult | null>(null);
  const [syncProgress, setSyncProgress] = useState<SyncJobProgress | null>(
    null
  );
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Field choices for account creation
  const [accountTypeOptions, setAccountTypeOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [entityOptions, setEntityOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);

  const {
    openTellerConnect,
    loading: tellerLoading,
    error: tellerError,
    clearError: clearTellerError,
  } = useTellerConnect();

  // Group accounts by type
  const bankAccounts = accounts.filter(
    acc => acc.account_type === 'checking' || acc.account_type === 'savings'
  );
  const creditCards = accounts.filter(acc => acc.account_type === 'credit_card');

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await transactionsApiService.getAccounts();
      setAccounts(data);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const fetchFieldChoices = async () => {
    try {
      const choices = await transactionsApiService.getAccountFieldChoices();
      setAccountTypeOptions(choices.type || []);
      setEntityOptions(choices.entity || []);
    } catch (e: any) {
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
    if (tellerError) {
      setError(tellerError);
      clearTellerError();
    }
  }, [tellerError, clearTellerError]);

  // Polling for sync progress
  const pollSyncProgress = useCallback(async (connectionId: number) => {
    try {
      const progress = await tellerApiService.getSyncJobProgress(connectionId);
      if (progress) {
        setSyncProgress(progress);
        if (progress.status !== 'running') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setSyncLoading(false);
          if (progress.status === 'completed') {
            setSyncResult({
              success: true,
              accounts_synced: 1,
              transactions_synced: progress.transactions_synced,
              errors: [],
              message: `Synced ${progress.transactions_synced} transactions`,
            });
          } else if (progress.status === 'failed') {
            setSyncResult({
              success: false,
              accounts_synced: 0,
              transactions_synced: 0,
              errors: progress.errors || ['Sync failed'],
              message: 'Sync failed',
            });
          }
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
        asset_entity_name: form.entity,
      });
      await refresh();
      setShowCreate(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (form: {
    name: string;
    type: string;
    entity: string;
  }) => {
    if (!selectedAccount) return;
    try {
      setLoading(true);
      await transactionsApiService.updateAccount(selectedAccount.id, {
        name: form.name,
        type: form.type,
        asset_entity_name: form.entity,
      });
      await refresh();
      setShowDetail(false);
      setSelectedAccount(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to update account');
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
    } catch (e: any) {
      setError(e?.message ?? 'Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!selectedAccount?.connection_id) return;

    setSyncLoading(true);
    setSyncResult(null);
    setSyncProgress(null);
    setShowDetail(false);
    setShowSync(true);

    try {
      const result = await tellerApiService.syncTellerConnection(
        selectedAccount.connection_id
      );
      setSyncResult(result);

      // Start polling for progress
      pollIntervalRef.current = setInterval(() => {
        pollSyncProgress(selectedAccount.connection_id!);
      }, 1000);
    } catch (e: any) {
      setSyncResult({
        success: false,
        accounts_synced: 0,
        transactions_synced: 0,
        errors: [e?.message || 'Unknown error'],
        message: 'Sync failed',
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
      await tellerApiService.deleteTellerConnection(
        selectedAccount.connection_id,
        deleteData
      );
      await refresh();
      setShowDisconnect(false);
      setSelectedAccount(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to disconnect');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectBank = () => {
    openTellerConnect(() => {
      refresh();
    });
  };

  const closeSync = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setShowSync(false);
    setSyncResult(null);
    setSyncProgress(null);
    refresh();
  };

  const renderAccountTile = (account: Account) => {
    const statusColors: Record<string, string> = {
      active: 'text-green-500',
      error: 'text-red-500',
      disconnected: 'text-gray-400',
    };

    return (
      <button
        key={account.id}
        type="button"
        onClick={() => handleAccountClick(account)}
        className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition relative group"
        aria-label={`Open ${account.name}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium mb-1 truncate">{account.name}</div>
            <div className="text-xs text-muted-foreground">
              {account.institution_name || account.entity_display || 'Manual'}
            </div>
            {account.account_number_last4 && (
              <div className="text-xs text-muted-foreground mt-1">
                ····{account.account_number_last4}
              </div>
            )}
          </div>
          {account.has_connection && (
            <div
              className={`flex items-center gap-1 ${statusColors[account.connection_status || 'active']}`}
              title={`Synced via Teller - ${account.connection_status}`}
            >
              <Cloud className="h-4 w-4" />
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
            <Button
              type="button"
              variant="outline"
              onClick={handleConnectBank}
              disabled={tellerLoading}
            >
              <Building2 className="h-4 w-4 mr-2" />
              Connect Bank
            </Button>
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
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {bankAccounts.map(renderAccountTile)}
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
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {creditCards.map(renderAccountTile)}
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
        loading={loading}
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

      {/* Sync Modal */}
      <TellerSyncModal
        isOpen={showSync}
        onClose={closeSync}
        loading={syncLoading}
        result={syncResult}
        progress={syncProgress}
      />
    </Card>
  );
}
