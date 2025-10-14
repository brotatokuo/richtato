import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Modal } from '@/components/ui/Modal';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

export function AccountsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: '',
    type: 'checking',
    entity: 'other',
  });

  const accountTypeOptions = [
    'checking',
    'savings',
    'retirement',
    'investment',
  ];
  const entityOptions = [
    'bank_of_america',
    'chase',
    'citibank',
    'marcus',
    'other',
  ];

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

  useEffect(() => {
    refresh();
  }, []);

  const openCreate = () => {
    setForm({ name: '', type: 'checking', entity: 'other' });
    setShowCreate(true);
  };

  const submitCreate = async () => {
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

  const openEdit = (acc: Account) => {
    setSelectedId(acc.id);
    setForm({
      name: acc.name,
      type: (acc as any).type
        ? String((acc as any).type).toLowerCase()
        : 'checking',
      entity: (acc as any).entity
        ? String((acc as any).entity).toLowerCase()
        : 'other',
    });
    setShowEdit(true);
  };

  const submitEdit = async () => {
    if (selectedId == null) return;
    try {
      setLoading(true);
      const payload: any = {
        name: form.name,
        type: form.type,
        asset_entity_name: form.entity,
      };
      await transactionsApiService.updateAccount(selectedId, payload);
      await refresh();
      setShowEdit(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to update account');
    } finally {
      setLoading(false);
    }
  };

  const submitDelete = async () => {
    if (selectedId == null) return;
    try {
      setLoading(true);
      await transactionsApiService.deleteAccount(selectedId);
      await refresh();
      setShowDelete(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Accounts</CardTitle>
            <CardDescription>All financial accounts on file</CardDescription>
          </div>
          <Button type="button" variant="outline" onClick={openCreate}>
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
              <button
                key={acc.id}
                type="button"
                onClick={() => openEdit(acc)}
                className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition"
                aria-label={`Open ${acc.name}`}
              >
                <div className="text-sm font-medium mb-1">{acc.name}</div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {((acc as any).type || (acc as any).entity) && (
                    <>
                      {(acc as any).type && (
                        <Badge variant="outline">{(acc as any).type}</Badge>
                      )}
                      {(acc as any).entity && (
                        <Badge variant="outline">{(acc as any).entity}</Badge>
                      )}
                    </>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>

      {/* Create Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create Account"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="acc-name">Name</Label>
            <Input
              id="acc-name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Main Checking"
            />
          </div>
          <div>
            <Label htmlFor="acc-type">Type</Label>
            <Select
              value={form.type}
              onValueChange={v => setForm({ ...form, type: v })}
            >
              <SelectTrigger id="acc-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {accountTypeOptions.map(t => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="acc-entity">Bank/Entity</Label>
            <Select
              value={form.entity}
              onValueChange={v => setForm({ ...form, entity: v })}
            >
              <SelectTrigger id="acc-entity">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {entityOptions.map(e => (
                  <SelectItem key={e} value={e}>
                    {e}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button onClick={submitCreate} disabled={!form.name}>
              Create
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        title="Edit Account"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="edit-acc-name">Name</Label>
            <Input
              id="edit-acc-name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="edit-acc-type">Type</Label>
            <Select
              value={form.type}
              onValueChange={v => setForm({ ...form, type: v })}
            >
              <SelectTrigger id="edit-acc-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {accountTypeOptions.map(t => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="edit-acc-entity">Bank/Entity</Label>
            <Select
              value={form.entity}
              onValueChange={v => setForm({ ...form, entity: v })}
            >
              <SelectTrigger id="edit-acc-entity">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {entityOptions.map(e => (
                  <SelectItem key={e} value={e}>
                    {e}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-between gap-2">
            <Button
              variant="destructive"
              onClick={() => {
                setShowEdit(false);
                if (selectedId != null) setShowDelete(true);
              }}
            >
              Delete
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowEdit(false)}>
                Cancel
              </Button>
              <Button onClick={submitEdit} disabled={!form.name}>
                Save
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Delete Modal */}
      <Modal
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        title="Delete Account"
      >
        <div className="space-y-4">
          <p>Are you sure you want to delete this account?</p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowDelete(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={submitDelete}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
}
