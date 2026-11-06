import type { GameState, PlayerView } from '../lib/protocol.ts';

export function player(name: string, overrides: Partial<PlayerView> = {}): PlayerView {
  return { name, played: [], hand_size: 10, has_played: false, pudding: 0, scores: [], ...overrides };
}

export function gameState(overrides: Partial<GameState> = {}): GameState {
  return {
    game: 'g',
    status: 'playing',
    round: 1,
    max_rounds: 3,
    you: 'alice',
    hand: [{ type: 'TempuraCard' }, { type: 'SquidNigiriCard', wasabi: false }, { type: 'ThreeRollMakiCard', rolls: 3 }],
    can_play: true,
    can_use_chopsticks: false,
    players: [player('alice'), player('bob')],
    last_round: null,
    final_scores: null,
    ...overrides,
  };
}
