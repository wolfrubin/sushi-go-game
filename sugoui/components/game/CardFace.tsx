import React from 'react';
import { cardInfo, cardLabel } from '../../lib/cards';
import type { CardView } from '../../lib/protocol';

interface CardFaceProps {
  card: CardView;
  selected?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  small?: boolean;
}

export function CardFace({ card, selected, onClick, disabled, small }: CardFaceProps) {
  const { name, emoji, hint } = cardInfo(card);
  const classes = ['sg-card', small ? 'sg-card-small' : '', selected ? 'sg-card-selected' : '', card.wasabi ? 'sg-card-wasabi' : '']
    .filter(Boolean)
    .join(' ');
  const content = (
    <>
      <span className="sg-card-emoji" aria-hidden="true">{emoji}</span>
      <span className="sg-card-name">{name}</span>
      {card.wasabi && <span className="sg-card-tag">+ wasabi</span>}
    </>
  );
  if (!onClick) {
    return <span className={classes} title={hint} aria-label={cardLabel(card)} role="img">{content}</span>;
  }
  return (
    <button
      type="button"
      className={classes}
      title={hint}
      aria-pressed={!!selected}
      aria-label={cardLabel(card)}
      disabled={disabled}
      onClick={onClick}
    >
      {content}
    </button>
  );
}
