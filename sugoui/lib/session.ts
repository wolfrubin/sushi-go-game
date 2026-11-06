import type { Session } from './protocol.ts';

const SESSION_KEY = 'sugo.session';
const NAME_KEY = 'sugo.playerName';

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function defaultStorage(): StorageLike | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null;
  } catch {
    return null; // storage can be blocked (private mode, cookies disabled)
  }
}

function isSession(value: unknown): value is Session {
  const v = value as Session;
  return !!v && typeof v.game === 'string' && typeof v.player === 'string' && typeof v.token === 'string';
}

/** Remembers who you are in which game so a refresh or dropped connection can resume. */
export function loadSession(storage: StorageLike | null = defaultStorage()): Session | null {
  try {
    const raw = storage?.getItem(SESSION_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    return isSession(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveSession(session: Session, storage: StorageLike | null = defaultStorage()): void {
  try {
    storage?.setItem(SESSION_KEY, JSON.stringify(session));
    storage?.setItem(NAME_KEY, session.player);
  } catch {
    /* resuming after a refresh just won't work */
  }
}

export function clearSession(storage: StorageLike | null = defaultStorage()): void {
  try {
    storage?.removeItem(SESSION_KEY);
  } catch {
    /* nothing to do */
  }
}

export function loadPlayerName(storage: StorageLike | null = defaultStorage()): string {
  try {
    return storage?.getItem(NAME_KEY) ?? '';
  } catch {
    return '';
  }
}
