import type { CardView } from './protocol.ts';

interface CardInfo {
  name: string;
  emoji: string;
  hint: string;
}

const CARDS: Record<string, CardInfo> = {
  TempuraCard: { name: 'Tempura', emoji: '🍤', hint: '5 points for every pair' },
  SashimiCard: { name: 'Sashimi', emoji: '🐟', hint: '10 points for every set of 3' },
  DumplingCard: { name: 'Dumpling', emoji: '🥟', hint: '1, 3, 6, 10, 15 points for 1 to 5' },
  EggNigiriCard: { name: 'Egg Nigiri', emoji: '🥚', hint: '1 point' },
  SalmonNigiriCard: { name: 'Salmon Nigiri', emoji: '🍣', hint: '2 points' },
  SquidNigiriCard: { name: 'Squid Nigiri', emoji: '🦑', hint: '3 points' },
  WasabiCard: { name: 'Wasabi', emoji: '🌿', hint: 'Triples the next nigiri you play' },
  ChopsticksCard: { name: 'Chopsticks', emoji: '🥢', hint: 'Play two cards in a later turn' },
  PuddingCard: { name: 'Pudding', emoji: '🍮', hint: 'Scored at the end of the game' },
  OneRollMakiCard: { name: 'Maki ×1', emoji: '🍙', hint: 'Most maki rolls scores 6, second 3' },
  TwoRollMakiCard: { name: 'Maki ×2', emoji: '🍙', hint: 'Most maki rolls scores 6, second 3' },
  ThreeRollMakiCard: { name: 'Maki ×3', emoji: '🍙', hint: 'Most maki rolls scores 6, second 3' },
};

export function cardInfo(card: CardView): CardInfo {
  return (
    CARDS[card.type] ?? {
      name: card.type.replace(/Card$/, ''),
      emoji: '🍽️',
      hint: '',
    }
  );
}

/** Plain text name for screen readers and tooltips. */
export function cardLabel(card: CardView): string {
  const { name } = cardInfo(card);
  return card.wasabi ? `${name} with wasabi` : name;
}

export function sum(numbers: number[]): number {
  return numbers.reduce((total, n) => total + n, 0);
}

/** Everyone sharing the highest score. */
export function winners(finalScores: Record<string, number>): string[] {
  const best = Math.max(...Object.values(finalScores));
  return Object.keys(finalScores).filter((name) => finalScores[name] === best);
}

/** The server accepts one index, or two comma separated when using chopsticks. */
export function playBody(selected: number[]): number | number[] {
  return selected.length === 1 ? selected[0] : selected;
}
