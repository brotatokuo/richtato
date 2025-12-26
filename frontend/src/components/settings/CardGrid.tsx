import { CardAccountItem } from '@/hooks/useCards';
import {
  getBankLogo,
  getCardImage,
  hasSpecificCardImage,
} from '@/lib/imageMapping';
import { useState } from 'react';

interface CardGridProps {
  cards: CardAccountItem[];
  loading: boolean;
  onCardClick: (card: CardAccountItem) => void;
}

function CreditCardItem({
  card,
  onCardClick,
}: {
  card: CardAccountItem;
  onCardClick: (card: CardAccountItem) => void;
}) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const hasSpecificImage = hasSpecificCardImage(card.name, card.imageKey);
  const cardImage = hasSpecificImage
    ? getCardImage(card.name, card.bank, card.imageKey)
    : '/images/credit_cards/default.png';
  const bankLogo = getBankLogo(card.bank);

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMousePosition({ x, y });
  };

  const handleMouseEnter = () => setIsHovering(true);
  const handleMouseLeave = () => setIsHovering(false);

  return (
    <button
      type="button"
      onClick={() => onCardClick(card)}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="rounded-xl relative overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-xl group"
      style={{
        aspectRatio: '1.586',
        width: '100%',
        maxWidth: '200px',
      }}
      aria-label={`Open ${card.name}`}
    >
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
          <div className="text-xs font-semibold text-white drop-shadow-lg relative z-10">
            {card.name}
          </div>
        )}

        {/* Bank Logo at Bottom Right (only show when using default background) */}
        {!hasSpecificImage && bankLogo && (
          <div className="flex justify-end items-end">
            <img
              src={bankLogo}
              alt={`${card.bank} logo`}
              className="w-8 h-8 object-contain drop-shadow-md relative z-10"
            />
          </div>
        )}
      </div>
    </button>
  );
}

export function CardGrid({ cards, loading, onCardClick }: CardGridProps) {
  if (loading) {
    return <div className="text-sm">Loading…</div>;
  }

  if (cards.length === 0) {
    return <div className="text-sm text-muted-foreground">No cards</div>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map(card => (
        <CreditCardItem
          key={card.id}
          card={card}
          onCardClick={onCardClick}
        />
      ))}
    </div>
  );
}
