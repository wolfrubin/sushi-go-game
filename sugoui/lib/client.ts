import type { Action, GameState, Reply, Session } from './protocol.ts';

export type ConnectionStatus = 'connecting' | 'open' | 'closed';

export interface Snapshot {
  status: ConnectionStatus;
  state: GameState | null;
  /** True when the server no longer knows our session (game expired, bad token). */
  sessionLost: boolean;
}

/** The subset of the browser WebSocket we use, so tests can fake it. */
export interface SocketLike {
  /** Browser WebSocket states: 0 connecting, 1 open, 2 closing, 3 closed. */
  readyState?: number;
  send(data: string): void;
  close(): void;
  onopen: ((event: unknown) => void) | null;
  onclose: ((event: unknown) => void) | null;
  onmessage: ((event: { data: unknown }) => void) | null;
  onerror: ((event: unknown) => void) | null;
}

export interface ClientOptions {
  url: string;
  createSocket?: (url: string) => SocketLike;
  /** Delays between reconnect attempts; the last one repeats. */
  retryDelaysMs?: number[];
  requestTimeoutMs?: number;
}

interface Pending {
  resolve: (reply: Reply) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

const DEFAULT_RETRY_DELAYS = [500, 1000, 2000, 4000, 8000];
// Errors that mean our saved session can never work again
const SESSION_LOST = /invalid token|does not exist|is not in game/i;

/**
 * Talks to the game server. Matches replies to requests, keeps the latest
 * game state pushed by the server, reconnects with backoff, and re-attaches
 * to the saved session after reconnecting.
 */
export class SugoClient {
  private options: Required<Omit<ClientOptions, 'url'>> & { url: string };
  private socket: SocketLike | null = null;
  private pending = new Map<number, Pending>();
  private listeners = new Set<() => void>();
  private nextId = 1;
  private retryCount = 0;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private wantOpen = false;
  private session: Session | null = null;
  private snapshot: Snapshot = { status: 'closed', state: null, sessionLost: false };

  constructor(options: ClientOptions) {
    this.options = {
      createSocket: (url) => new WebSocket(url) as unknown as SocketLike,
      retryDelaysMs: DEFAULT_RETRY_DELAYS,
      requestTimeoutMs: 10000,
      ...options,
    };
  }

  /** The address is only known in the browser, so it can be set after construction. */
  setUrl(url: string) {
    this.options.url = url;
  }

  // ---- observable state (works with React's useSyncExternalStore) ----

  getSnapshot = (): Snapshot => this.snapshot;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private update(changes: Partial<Snapshot>) {
    this.snapshot = { ...this.snapshot, ...changes };
    this.listeners.forEach((listener) => listener());
  }

  // ---- connection ----

  connect() {
    this.wantOpen = true;
    if (this.socket) return;
    this.update({ status: 'connecting' });
    const socket = this.options.createSocket(this.options.url);
    this.socket = socket;
    socket.onopen = () => {
      this.retryCount = 0;
      this.update({ status: 'open' });
      void this.resume();
    };
    socket.onmessage = (event) => this.handleMessage(event.data);
    socket.onclose = () => this.handleClose(socket);
    socket.onerror = () => {
      /* onclose always follows and drives reconnection */
    };
  }

  close() {
    this.wantOpen = false;
    if (this.retryTimer) clearTimeout(this.retryTimer);
    this.retryTimer = null;
    this.socket?.close();
  }

  private handleClose(socket: SocketLike) {
    if (this.socket !== socket) return;
    this.socket = null;
    this.rejectAllPending(new Error('Connection lost'));
    this.update({ status: this.wantOpen ? 'connecting' : 'closed' });
    if (!this.wantOpen) return;
    const delays = this.options.retryDelaysMs;
    const delay = delays[Math.min(this.retryCount, delays.length - 1)];
    this.retryCount += 1;
    this.retryTimer = setTimeout(() => {
      this.retryTimer = null;
      if (this.wantOpen) this.connect();
    }, delay);
  }

  // ---- session ----

  /** Set (or clear with null) who we are. Reconnects re-attach to this session. */
  setSession(session: Session | null) {
    this.session = session;
    this.update({ sessionLost: false, ...(session ? {} : { state: null }) });
    if (session && this.snapshot.status === 'open') void this.resume();
  }

  private async resume() {
    const session = this.session;
    if (!session) return;
    try {
      const reply = await this.request('GAME_STATE', { ...session });
      if (this.session === session && reply.state) this.update({ state: reply.state });
    } catch (error) {
      if (this.session === session && SESSION_LOST.test((error as Error).message)) {
        this.update({ sessionLost: true });
      }
      // other failures (e.g. connection dropped) are retried on reconnect
    }
  }

  // ---- requests ----

  /** Sends an action and resolves with the reply. Rejects with the server's message on failure. */
  request(action: Action, fields: Record<string, unknown> = {}): Promise<Reply> {
    return new Promise((resolve, reject) => {
      // A closing socket silently drops what it is sent, so refuse up front
      const socketOpen = this.socket !== null && (this.socket.readyState === undefined || this.socket.readyState === 1);
      if (!socketOpen || this.snapshot.status !== 'open') {
        reject(new Error('Not connected to the game server'));
        return;
      }
      const id = this.nextId++;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('The game server took too long to answer'));
      }, this.options.requestTimeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.socket.send(JSON.stringify({ id, action, ...fields }));
    });
  }

  /** An action for the session we are currently in (adds game, player and token). */
  act(action: Action, body?: number | number[]): Promise<Reply> {
    if (!this.session) return Promise.reject(new Error('Not in a game'));
    const { game, player, token } = this.session;
    return this.request(action, { game, player, token, ...(body === undefined ? {} : { body }) });
  }

  private handleMessage(data: unknown) {
    let message: Reply & { event?: string };
    try {
      message = JSON.parse(String(data));
    } catch {
      return; // ignore anything that isn't JSON
    }
    if (message.event === 'state') {
      const state = (message as unknown as { state: GameState }).state;
      // Only show state for the game we are in
      if (this.session && state.game === this.session.game && state.you === this.session.player) {
        this.update({ state });
      }
      return;
    }
    if (typeof message.id !== 'number') return;
    const pending = this.pending.get(message.id);
    if (!pending) return;
    this.pending.delete(message.id);
    clearTimeout(pending.timer);
    if (message.ok) pending.resolve(message);
    else pending.reject(new Error(message.error ?? 'Request failed'));
  }

  private rejectAllPending(error: Error) {
    this.pending.forEach((pending) => {
      clearTimeout(pending.timer);
      pending.reject(error);
    });
    this.pending.clear();
  }
}

/** Where the browser should connect: same host as the page, under the app's base path. */
export function defaultSocketUrl(location: { protocol: string; host: string; hostname: string }): string {
  const override = process.env.NEXT_PUBLIC_SUGO_WS_URL;
  if (override) return override;
  // During `next dev` the UI and the game server are on different ports
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    return `ws://${location.hostname}:4137`;
  }
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${location.host}${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/ws`;
}
