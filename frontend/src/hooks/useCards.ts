import { cardsApi } from '@/lib/api/user';
import { useEffect, useState } from 'react';

export interface CardAccountItem {
  id: number;
  name: string;
  bank: string;
}

interface BankOption {
  value: string;
  label: string;
}

export function useCards() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cards, setCards] = useState<CardAccountItem[]>([]);
  const [bankOptions, setBankOptions] = useState<BankOption[]>([]);

  const refresh = async () => {
    try {
      setLoading(true);
      const data = await cardsApi.list();
      setCards(data);
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load cards');
      setCards([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchFieldChoices = async () => {
    try {
      const choices = await cardsApi.getFieldChoices();
      setBankOptions(choices.bank || []);
    } catch (e: unknown) {
      setError((e as Error).message ?? 'Failed to load field choices');
    }
  };

  const createCard = async (name: string, bank: string) => {
    try {
      setLoading(true);
      await cardsApi.create({ name, bank });
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? 'Failed to create card');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const updateCard = async (id: number, name: string, bank: string) => {
    try {
      setLoading(true);
      await cardsApi.update(id, { name, bank });
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? 'Failed to update card');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const deleteCard = async (id: number) => {
    try {
      setLoading(true);
      await cardsApi.remove(id);
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? 'Failed to delete card');
      throw e;
    } finally {
      setLoading(false);
    }
  };

  const getBankLabel = (value: string): string => {
    const option = bankOptions.find(opt => opt.value === value);
    return option?.label || value;
  };

  useEffect(() => {
    refresh();
    fetchFieldChoices();
  }, []);

  return {
    cards,
    loading,
    error,
    bankOptions,
    createCard,
    updateCard,
    deleteCard,
    getBankLabel,
    refresh,
  };
}
