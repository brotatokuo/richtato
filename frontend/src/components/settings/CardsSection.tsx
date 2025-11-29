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
import { cardsApi } from '@/lib/api/user';
import { CreditCard, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

interface CardAccountItem {
  id: number;
  name: string;
  bank: string;
}

export function CardsSection() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cards, setCards] = useState<CardAccountItem[]>([]);

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: '', bank: 'other' });
  const bankOptions = [
    'american_express',
    'bank_of_america',
    'bilt',
    'chase',
    'citibank',
    'other',
  ];

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await cardsApi.list();
      setCards(data);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load cards');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const openCreate = () => {
    setForm({ name: '', bank: 'other' });
    setShowCreate(true);
  };

  const submitCreate = async () => {
    try {
      setLoading(true);
      await cardsApi.create({ name: form.name, bank: form.bank });
      await refresh();
      setShowCreate(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to create card');
    } finally {
      setLoading(false);
    }
  };

  const openEdit = (card: CardAccountItem) => {
    setSelectedId(card.id);
    setForm({ name: card.name, bank: String(card.bank).toLowerCase() });
    setShowEdit(true);
  };

  const submitEdit = async () => {
    if (selectedId == null) return;
    try {
      setLoading(true);
      await cardsApi.update(selectedId, { name: form.name, bank: form.bank });
      await refresh();
      setShowEdit(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to update card');
    } finally {
      setLoading(false);
    }
  };

  const submitDelete = async () => {
    if (selectedId == null) return;
    try {
      setLoading(true);
      await cardsApi.remove(selectedId);
      await refresh();
      setShowDelete(false);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to delete card');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Cards
            </CardTitle>
            <CardDescription>Linked card accounts</CardDescription>
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
        ) : cards.length === 0 ? (
          <div className="text-sm text-muted-foreground">No cards</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {cards.map(card => (
              <button
                key={card.id}
                type="button"
                onClick={() => openEdit(card)}
                className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition"
                aria-label={`Open ${card.name}`}
              >
                <div className="text-sm font-medium mb-1">{card.name}</div>
                <div className="text-xs text-muted-foreground">
                  <Badge variant="outline">{card.bank}</Badge>
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Add Card"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="card-name">Name</Label>
            <Input
              id="card-name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Sapphire Preferred"
            />
          </div>
          <div>
            <Label htmlFor="card-bank">Bank</Label>
            <Select
              value={form.bank}
              onValueChange={v => setForm({ ...form, bank: v })}
            >
              <SelectTrigger id="card-bank">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {bankOptions.map(b => (
                  <SelectItem key={b} value={b}>
                    {b}
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
              Add
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        title="Edit Card"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="edit-card-name">Name</Label>
            <Input
              id="edit-card-name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="edit-card-bank">Bank</Label>
            <Select
              value={form.bank}
              onValueChange={v => setForm({ ...form, bank: v })}
            >
              <SelectTrigger id="edit-card-bank">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {bankOptions.map(b => (
                  <SelectItem key={b} value={b}>
                    {b}
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

      <Modal
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        title="Delete Card"
      >
        <div className="space-y-4">
          <p>Are you sure you want to delete this card?</p>
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
