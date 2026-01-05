import { AccountCard } from '@/components/accounts/AccountCard';
import { AccountCreateModal } from '@/components/accounts/AccountCreateModal';
import { AccountDeleteModal } from '@/components/accounts/AccountDeleteModal';
import { AccountEditModal } from '@/components/accounts/AccountEditModal';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { Landmark, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

export function AccountsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const [accountTypeOptions, setAccountTypeOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [entityOptions, setEntityOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await transactionsApiService.getAccounts();
      setAccounts(data);
      setError(null);
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to load accounts');
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
      // Set default options if fetch fails
      setAccountTypeOptions([
        { value: 'checking', label: 'Checking' },
        { value: 'savings', label: 'Savings' },
        { value: 'retirement', label: 'Retirement' },
        { value: 'investment', label: 'Investment' },
      ]);
      setEntityOptions([
        { value: 'bank_of_america', label: 'Bank of America' },
        { value: 'chase', label: 'Chase' },
        { value: 'citibank', label: 'Citibank' },
        { value: 'marcus', label: 'Marcus by Goldman Sachs' },
        { value: 'other', label: 'Other' },
      ]);
    }
  };

  useEffect(() => {
    refresh();
    fetchFieldChoices();
  }, []);

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
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (form: {
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
      setShowEdit(false);
      setSelectedAccount(null);
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to update account');
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
      setShowDelete(false);
      setSelectedAccount(null);
    } catch (e: unknown) {
      setError((e as Error)?.message ?? 'Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  const openEdit = (account: Account) => {
    setSelectedAccount(account);
    setShowEdit(true);
  };

  const openDelete = () => {
    setShowDelete(true);
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
            <CardDescription>All financial accounts on file</CardDescription>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowCreate(true)}
          >
            <Plus className="h-4 w-4 mr-2" /> Add
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
        {loading ? (
          <div className="text-sm">Loading…</div>
        ) : accounts.length === 0 ? (
          <div className="text-sm text-muted-foreground">No accounts</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {accounts.map(acc => (
              <AccountCard key={acc.id} account={acc} onClick={openEdit} />
            ))}
          </div>
        )}
      </CardContent>

      <AccountCreateModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={loading}
      />

      <AccountEditModal
        isOpen={showEdit}
        onClose={() => {
          setShowEdit(false);
          setSelectedAccount(null);
        }}
        onSubmit={handleEdit}
        onDelete={openDelete}
        initialValues={{
          name: selectedAccount?.name || '',
          type: selectedAccount?.type || 'checking',
          entity: selectedAccount?.entity || 'other',
        }}
        accountTypeOptions={accountTypeOptions}
        entityOptions={entityOptions}
        loading={loading}
      />

      <AccountDeleteModal
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={handleDelete}
        loading={loading}
      />
    </Card>
  );
}
