import { CardAccountItem } from '@/hooks/useCards';

interface CardGridProps {
  cards: CardAccountItem[];
  loading: boolean;
  onCardClick: (card: CardAccountItem) => void;
}

export function CardGrid({ cards, loading, onCardClick }: CardGridProps) {
  if (loading) {
    return <div className="text-sm">Loading…</div>;
  }

  if (cards.length === 0) {
    return <div className="text-sm text-muted-foreground">No cards</div>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {cards.map(card => (
        <button
          key={card.id}
          type="button"
          onClick={() => onCardClick(card)}
          className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition"
          aria-label={`Open ${card.name}`}
        >
          <div className="text-sm font-medium mb-1">{card.name}</div>
        </button>
      ))}
    </div>
  );
}
