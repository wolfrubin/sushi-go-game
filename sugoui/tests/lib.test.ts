import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { cardInfo, cardLabel, playBody, sum, winners } from '../lib/cards.ts';
import { clearSession, loadPlayerName, loadSession, saveSession } from '../lib/session.ts';

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, value),
    removeItem: (key: string) => void data.delete(key),
    data,
  };
}

const brokenStorage = {
  getItem: () => { throw new Error('blocked'); },
  setItem: () => { throw new Error('blocked'); },
  removeItem: () => { throw new Error('blocked'); },
};

describe('cards', () => {
  it('knows every card the server can send', () => {
    const types = ['TempuraCard', 'SashimiCard', 'DumplingCard', 'EggNigiriCard', 'SalmonNigiriCard', 'SquidNigiriCard',
      'WasabiCard', 'ChopsticksCard', 'PuddingCard', 'OneRollMakiCard', 'TwoRollMakiCard', 'ThreeRollMakiCard'];
    for (const type of types) {
      const info = cardInfo({ type });
      assert.ok(info.emoji && info.hint, type);
      assert.ok(!info.name.endsWith('Card'), type);
    }
  });

  it('falls back gracefully for unknown cards', () => {
    assert.equal(cardInfo({ type: 'MysteryCard' }).name, 'Mystery');
  });

  it('labels wasabi nigiri', () => {
    assert.equal(cardLabel({ type: 'SquidNigiriCard' }), 'Squid Nigiri');
    assert.equal(cardLabel({ type: 'SquidNigiriCard', wasabi: true }), 'Squid Nigiri with wasabi');
  });

  it('sums scores', () => {
    assert.equal(sum([]), 0);
    assert.equal(sum([5, -6, 10]), 9);
  });

  it('finds winners including ties', () => {
    assert.deepEqual(winners({ a: 10, b: 20, c: 5 }), ['b']);
    assert.deepEqual(winners({ a: 20, b: 20 }), ['a', 'b']);
    assert.deepEqual(winners({ a: -3 }), ['a']);
  });

  it('builds the play body', () => {
    assert.equal(playBody([4]), 4);
    assert.deepEqual(playBody([1, 7]), [1, 7]);
  });
});

describe('session storage', () => {
  const session = { game: 'g', player: 'alice', token: 't' };

  it('round trips and remembers the player name', () => {
    const storage = memoryStorage();
    saveSession(session, storage);
    assert.deepEqual(loadSession(storage), session);
    assert.equal(loadPlayerName(storage), 'alice');
  });

  it('keeps the player name after the session is cleared', () => {
    const storage = memoryStorage();
    saveSession(session, storage);
    clearSession(storage);
    assert.equal(loadSession(storage), null);
    assert.equal(loadPlayerName(storage), 'alice');
  });

  it('rejects corrupt or incomplete stored sessions', () => {
    for (const raw of ['not json', '{}', '{"game":"g"}', '[]', 'null', '{"game":1,"player":"a","token":"t"}']) {
      assert.equal(loadSession(memoryStorage({ 'sugo.session': raw })), null, raw);
    }
  });

  it('survives blocked storage', () => {
    assert.equal(loadSession(brokenStorage), null);
    assert.equal(loadPlayerName(brokenStorage), '');
    assert.doesNotThrow(() => saveSession(session, brokenStorage));
    assert.doesNotThrow(() => clearSession(brokenStorage));
  });

  it('survives missing storage (server side rendering)', () => {
    assert.equal(loadSession(null), null);
    assert.equal(loadPlayerName(null), '');
    assert.doesNotThrow(() => saveSession(session, null));
  });
});
