// Types for the JSON messages exchanged with the game server.
// See server/gateway.py in the backend for the full protocol.

export interface CardView {
  type: string;
  wasabi?: boolean; // nigiri only: has a wasabi on it
  rolls?: number; // maki only
}

export interface PlayerView {
  name: string;
  played: CardView[];
  hand_size: number;
  has_played: boolean;
  pudding: number;
  scores: number[];
}

export interface RoundSummary {
  number: number;
  players: Record<string, { played: CardView[]; score: number }>;
}

export type GameStatus = 'lobby' | 'playing' | 'finished';

export interface GameState {
  game: string;
  status: GameStatus;
  round: number;
  max_rounds: number;
  you: string;
  hand: CardView[];
  can_play: boolean;
  can_use_chopsticks: boolean;
  players: PlayerView[];
  last_round: RoundSummary | null;
  final_scores: Record<string, number> | null;
}

export interface GameListing {
  name: string;
  players: string[];
  status: GameStatus;
}

export interface Reply {
  id: number | string | null;
  ok: boolean;
  error?: string;
  token?: string;
  state?: GameState;
  games?: GameListing[];
}

export type Action = 'LIST_GAMES' | 'CREATE_GAME' | 'JOIN_GAME' | 'START_GAME' | 'PLAY_CARD' | 'GAME_STATE';

export interface Session {
  game: string;
  player: string;
  token: string;
}
