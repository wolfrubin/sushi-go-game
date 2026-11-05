import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { defaultSocketUrl, SugoClient } from '../lib/client.ts';
import type { SocketLike } from '../lib/client.ts';
import { gameState } from './fixtures.ts';

class FakeSocket implements SocketLike {
  readyState = 1;
  sent: any[] = [];
  closed = false;
  onopen: SocketLike['onopen'] = null;
  onclose: SocketLike['onclose'] = null;
  onmessage: SocketLike['onmessage'] = null;
  onerror: SocketLike['onerror'] = null;
  send(data: string) { this.sent.push(JSON.parse(data)); }
  close() { this.closed = true; this.onclose?.({}); }
  open() { this.onopen?.({}); }
  receive(message: unknown) { this.onmessage?.({ data: typeof message === 'string' ? message : JSON.stringify(message) }); }
  drop() { this.onclose?.({}); }
}

function setup(options: { retryDelaysMs?: number[]; requestTimeoutMs?: number } = {}) {
  const sockets: FakeSocket[] = [];
  const client = new SugoClient({
    url: 'ws://test',
    createSocket: () => { const s = new FakeSocket(); sockets.push(s); return s; },
    retryDelaysMs: [5],
    ...options,
  });
  return { client, sockets, socket: () => sockets[sockets.length - 1] };
}

const session = { game: 'g', player: 'alice', token: 'secret' };
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const tick = () => wait(0);

describe('connection', () => {
  it('goes connecting then open', () => {
    const { client, socket } = setup();
    assert.equal(client.getSnapshot().status, 'closed');
    client.connect();
    assert.equal(client.getSnapshot().status, 'connecting');
    socket().open();
    assert.equal(client.getSnapshot().status, 'open');
  });

  it('notifies subscribers and stops after unsubscribe', () => {
    const { client, socket } = setup();
    let calls = 0;
    const unsubscribe = client.subscribe(() => calls++);
    client.connect();
    socket().open();
    assert.equal(calls, 2);
    unsubscribe();
    socket().drop();
    assert.equal(calls, 2);
  });

  it('connect twice opens a single socket', () => {
    const { client, sockets } = setup();
    client.connect();
    client.connect();
    assert.equal(sockets.length, 1);
  });

  it('reconnects after the connection drops', async () => {
    const { client, sockets, socket } = setup();
    client.connect();
    socket().open();
    socket().drop();
    assert.equal(client.getSnapshot().status, 'connecting');
    await wait(30);
    assert.equal(sockets.length, 2);
    socket().open();
    assert.equal(client.getSnapshot().status, 'open');
  });

  it('backs off between attempts and resets after success', async () => {
    const { client, sockets, socket } = setup({ retryDelaysMs: [5, 60] });
    client.connect();
    socket().drop(); // attempt 1 fails -> wait 5
    await wait(25);
    assert.equal(sockets.length, 2);
    socket().drop(); // attempt 2 fails -> wait 60
    await wait(25);
    assert.equal(sockets.length, 2, 'second retry waits longer');
    await wait(80);
    assert.equal(sockets.length, 3);
    socket().open(); // success resets the backoff
    socket().drop();
    await wait(25);
    assert.equal(sockets.length, 4);
  });

  it('close() stops reconnecting', async () => {
    const { client, sockets, socket } = setup();
    client.connect();
    socket().open();
    client.close();
    await wait(30);
    assert.equal(sockets.length, 1);
    assert.equal(client.getSnapshot().status, 'closed');
  });

  it('close() while waiting to retry cancels the retry', async () => {
    const { client, sockets, socket } = setup();
    client.connect();
    socket().drop();
    client.close();
    await wait(30);
    assert.equal(sockets.length, 1);
  });
});

describe('requests', () => {
  it('sends an id and resolves with the matching reply', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    const promise = client.request('LIST_GAMES');
    const sent = socket().sent[0];
    assert.equal(sent.action, 'LIST_GAMES');
    assert.equal(typeof sent.id, 'number');
    socket().receive({ id: sent.id, ok: true, games: [] });
    assert.deepEqual((await promise).games, []);
  });

  it('matches out of order replies to the right request', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    const first = client.request('LIST_GAMES');
    const second = client.request('CREATE_GAME', { game: 'g', player: 'p' });
    const [a, b] = socket().sent;
    socket().receive({ id: b.id, ok: true, token: 'second' });
    socket().receive({ id: a.id, ok: true, games: [] });
    assert.equal((await second).token, 'second');
    assert.deepEqual((await first).games, []);
  });

  it('rejects with the server error message', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    const promise = client.request('JOIN_GAME', { game: 'g', player: 'p' });
    socket().receive({ id: socket().sent[0].id, ok: false, error: 'game is full' });
    await assert.rejects(promise, /game is full/);
  });

  it('rejects when not connected', async () => {
    const { client } = setup();
    await assert.rejects(client.request('LIST_GAMES'), /Not connected/);
    client.connect();
    await assert.rejects(client.request('LIST_GAMES'), /Not connected/); // still connecting
  });

  it('refuses to send on a socket that is closing', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    socket().readyState = 2; // closing: browsers would silently drop the message
    await assert.rejects(client.request('LIST_GAMES'), /Not connected/);
    assert.equal(socket().sent.length, 0);
  });

  it('rejects pending requests when the connection drops', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    const promise = client.request('LIST_GAMES');
    socket().drop();
    await assert.rejects(promise, /Connection lost/);
  });

  it('times out', async () => {
    const { client, socket } = setup({ requestTimeoutMs: 10 });
    client.connect();
    socket().open();
    await assert.rejects(client.request('LIST_GAMES'), /too long/);
  });

  it('ignores garbage, unknown ids and late replies', async () => {
    const { client, socket } = setup({ requestTimeoutMs: 10 });
    client.connect();
    socket().open();
    const promise = client.request('LIST_GAMES');
    socket().receive('not json {');
    socket().receive({ id: 9999, ok: true });
    socket().receive({ ok: true });
    await assert.rejects(promise, /too long/);
    socket().receive({ id: socket().sent[0].id, ok: true }); // arrives after timeout: harmless
  });

  it('act() adds the session credentials and body', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    await tick();
    socket().sent.length = 0;
    void client.act('PLAY_CARD', [3, 5]).catch(() => {});
    assert.deepEqual(socket().sent[0], { id: socket().sent[0].id, action: 'PLAY_CARD', ...session, body: [3, 5] });
    void client.act('START_GAME').catch(() => {});
    assert.equal('body' in socket().sent[1], false);
  });

  it('act() without a session rejects', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    await assert.rejects(client.act('START_GAME'), /Not in a game/);
  });
});

describe('state and sessions', () => {
  it('stores pushed state for the current session', () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ event: 'state', state: gameState() });
    assert.equal(client.getSnapshot().state?.game, 'g');
  });

  it('ignores pushes for other games or players', () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ event: 'state', state: gameState({ game: 'other' }) });
    socket().receive({ event: 'state', state: gameState({ you: 'bob' }) });
    assert.equal(client.getSnapshot().state, null);
  });

  it('ignores pushes when there is no session', () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    socket().receive({ event: 'state', state: gameState() });
    assert.equal(client.getSnapshot().state, null);
  });

  it('resumes the session as soon as it is set on an open connection', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    const sent = socket().sent[0];
    assert.deepEqual(sent, { id: sent.id, action: 'GAME_STATE', ...session });
    socket().receive({ id: sent.id, ok: true, state: gameState() });
    await tick();
    assert.equal(client.getSnapshot().state?.you, 'alice');
  });

  it('re-attaches to the session after reconnecting', async () => {
    const { client, sockets, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ id: socket().sent[0].id, ok: true, state: gameState() });
    await tick();
    socket().drop();
    await wait(30);
    socket().open();
    assert.equal(sockets.length, 2);
    assert.equal(socket().sent[0].action, 'GAME_STATE');
    assert.equal(socket().sent[0].token, 'secret');
  });

  it('keeps the last known state while reconnecting', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ event: 'state', state: gameState() });
    socket().drop();
    assert.equal(client.getSnapshot().status, 'connecting');
    assert.ok(client.getSnapshot().state);
  });

  it('flags a lost session when the token is refused', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ id: socket().sent[0].id, ok: false, error: 'invalid token for this player' });
    await tick();
    assert.equal(client.getSnapshot().sessionLost, true);
  });

  it('flags a lost session when the game has expired', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ id: socket().sent[0].id, ok: false, error: 'invalid token for this player' });
    await tick();
    client.setSession(null);
    assert.equal(client.getSnapshot().sessionLost, false);
    assert.equal(client.getSnapshot().state, null);
  });

  it('does not flag a lost session for transient failures', async () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().drop();
    await tick();
    assert.equal(client.getSnapshot().sessionLost, false);
  });

  it('clearing the session drops the state', () => {
    const { client, socket } = setup();
    client.connect();
    socket().open();
    client.setSession(session);
    socket().receive({ event: 'state', state: gameState() });
    client.setSession(null);
    assert.equal(client.getSnapshot().state, null);
  });
});

describe('defaultSocketUrl', () => {
  const at = (protocol: string, host: string, hostname = host.split(':')[0]) => ({ protocol, host, hostname });

  it('uses the dev server port on localhost', () => {
    assert.equal(defaultSocketUrl(at('http:', 'localhost:3000')), 'ws://localhost:4137');
    assert.equal(defaultSocketUrl(at('http:', '127.0.0.1:3000')), 'ws://127.0.0.1:4137');
  });

  it('uses wss on https sites, on the same host', () => {
    assert.equal(defaultSocketUrl(at('https:', 'wolfrub.in')), 'wss://wolfrub.in/ws');
  });

  it('uses ws on plain http hosts', () => {
    assert.equal(defaultSocketUrl(at('http:', 'example.test')), 'ws://example.test/ws');
  });

  it('honours an explicit override', () => {
    process.env.NEXT_PUBLIC_SUGO_WS_URL = 'wss://elsewhere.example/game';
    try {
      assert.equal(defaultSocketUrl(at('https:', 'wolfrub.in')), 'wss://elsewhere.example/game');
    } finally {
      delete process.env.NEXT_PUBLIC_SUGO_WS_URL;
    }
  });

  it('includes the base path', () => {
    process.env.NEXT_PUBLIC_BASE_PATH = '/sushi';
    try {
      assert.equal(defaultSocketUrl(at('https:', 'wolfrub.in')), 'wss://wolfrub.in/sushi/ws');
    } finally {
      delete process.env.NEXT_PUBLIC_BASE_PATH;
    }
  });
});
