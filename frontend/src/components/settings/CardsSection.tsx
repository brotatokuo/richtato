import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CardAccountItem, useCards } from '@/hooks/useCards';
import { CreditCard, Plus } from 'lucide-react';
import { useState } from 'react';
import { CardCreateModal } from './CardCreateModal';
import { CardDeleteModal } from './CardDeleteModal';
import { CardEditModal } from './CardEditModal';
import { CardGrid } from './CardGrid';

export function CardsSection() {
  const {
    cards,
    loading,
    error,
    bankOptions,
    createCard,
    updateCard,
    deleteCard,
  } = useCards();

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedCard, setSelectedCard] = useState<CardAccountItem | null>(
    null
  );

  const handleCardClick = (card: CardAccountItem) => {
    setSelectedCard(card);
    setShowEdit(true);
  };

  const handleCreate = async (name: string, bank: string) => {
    await createCard(name, bank);
  };

  const handleEdit = async (name: string, bank: string, imageKey: string | null) => {
    if (selectedCard) {
      await updateCard(selectedCard.id, name, bank, imageKey);
    }
  };

  const handleDelete = async () => {
    if (selectedCard) {
      await deleteCard(selectedCard.id);
    }
  };

  const openDeleteModal = () => {
    setShowEdit(false);
    setShowDelete(true);
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
        <CardGrid
          cards={cards}
          loading={loading}
          onCardClick={handleCardClick}
        />
      </CardContent>

      <CardCreateModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        bankOptions={bankOptions}
      />

      <CardEditModal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        onSubmit={handleEdit}
        onDelete={openDeleteModal}
        card={selectedCard}
        bankOptions={bankOptions}
      />

      <CardDeleteModal
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={handleDelete}
      />
    </Card>
  );
}
