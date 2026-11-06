import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { CardFace } from '../components/game/CardFace.tsx';
import { GameRoom } from '../components/game/GameRoom.tsx';
import { Lobby } from '../components/game/Lobby.tsx';
import { Scoreboard } from '../components/game/Scoreboard.tsx';
import { gameState, player } from './fixtures.ts';

const noop = async () => {};
const render = (element: React.ReactElement) => renderToStaticMarkup(element);
const room = (state = gameState()) => render(<GameRoom state={state} onStart={noop} onPlay={noop} onLeave={() => {}} />);

describe('CardFace', () => {
  it('renders a name, emoji and accessible label', () => {
    const html = render(<CardFace card={{ type: 'TempuraCard' }} />);
    assert.match(html, /Tempura/);
    assert.match(html, /aria-label="Tempura"/);
    assert.doesNotMatch(html, /<button/);
  });

  it('shows the wasabi tag', () => {
    const html = render(<CardFace card={{ type: 'SquidNigiriCard', wasabi: true }} />);
    assert.match(html, /\+ wasabi/);
    assert.match(html, /Squid Nigiri with wasabi/);
  });

  it('is a toggle button when clickable', () => {
    const html = render(<CardFace card={{ type: 'TempuraCard' }} onClick={() => {}} selected />);
    assert.match(html, /<button/);
    assert.match(html, /aria-pressed="true"/);
  });

  it('can be disabled', () => {
    assert.match(render(<CardFace card={{ type: 'TempuraCard' }} onClick={() => {}} disabled />), /disabled/);
  });
});

describe('Lobby', () => {
  const lobby = (games: any, extra: Partial<React.ComponentProps<typeof Lobby>> = {}) =>
    render(<Lobby games={games} initialName="alice" connected onCreate={noop} onJoin={noop} {...extra} />);

  it('shows a loading message before the games arrive', () => {
    assert.match(lobby(null), /Loading games/);
    assert.match(lobby(null, { connected: false }), /Waiting for the game server/);
  });

  it('invites you to create the first game', () => {
    assert.match(lobby([]), /No games yet/);
  });

  it('lists games and only offers Join for open ones', () => {
    const html = lobby([
      { name: 'open game', players: ['bob'], status: 'lobby' },
      { name: 'running', players: ['x', 'y'], status: 'playing' },
      { name: 'full', players: ['1', '2', '3', '4', '5'], status: 'lobby' },
    ]);
    assert.match(html, /open game/);
    assert.match(html, /bob/);
    assert.equal((html.match(/>Join</g) ?? []).length, 1);
    assert.match(html, /In progress/);
  });

  it('disables creating and joining without a name or connection', () => {
    const game = [{ name: 'g', players: ['bob'], status: 'lobby' }];
    assert.match(lobby(game, { initialName: '' }), /Enter your name/);
    assert.match(lobby(game, { initialName: '' }), /disabled=""[^>]*>Join/);
    assert.match(lobby(game, { connected: false }), /disabled=""[^>]*>Join/);
    assert.doesNotMatch(lobby(game), /disabled=""[^>]*>Join/);
  });

  it('escapes hostile game and player names', () => {
    const html = lobby([{ name: '<script>alert(1)</script>', players: ['<img src=x onerror=1>'], status: 'lobby' }]);
    assert.doesNotMatch(html, /<script>alert/);
    assert.doesNotMatch(html, /<img src=x/);
    assert.match(html, /&lt;script&gt;/);
  });
});

describe('GameRoom', () => {
  it('lobby: lists players and gates Start on two players', () => {
    const waiting = room(gameState({ status: 'lobby', hand: [], can_play: false, players: [player('alice')] }));
    assert.match(waiting, /Waiting for players \(1\/5\)/);
    assert.match(waiting, /disabled=""[^>]*>Start game/);
    const ready = room(gameState({ status: 'lobby', hand: [], can_play: false }));
    assert.doesNotMatch(ready, /disabled=""[^>]*>Start game/);
  });

  it('playing: shows round, hand and your turn', () => {
    const html = room();
    assert.match(html, /Round 1 of 3/);
    assert.match(html, /Your turn/);
    assert.match(html, /Tempura/);
    assert.match(html, /Squid Nigiri/);
    assert.match(html, /Maki ×3/);
    assert.match(html, /disabled=""[^>]*>Play card/); // nothing selected yet
  });

  it('playing: shows who you are waiting for and locks the hand', () => {
    const html = room(gameState({
      can_play: false,
      players: [player('alice', { has_played: true }), player('bob'), player('carol')],
    }));
    assert.match(html, /Waiting for bob, carol/);
    assert.doesNotMatch(html, /Your turn/);
    assert.match(html, /aria-pressed="false"[^>]*disabled=""/);
    assert.equal((html.match(/class="sg-card"[^>]*disabled=""/g) ?? []).length, 3);
  });

  it('only offers chopsticks when allowed', () => {
    assert.doesNotMatch(room(), /Use chopsticks/);
    assert.match(room(gameState({ can_use_chopsticks: true })), /Use chopsticks/);
  });

  it('shows opponents tables but never their hands', () => {
    const html = room(gameState({
      players: [player('alice'), player('bob', { played: [{ type: 'SalmonNigiriCard', wasabi: true }], hand_size: 9 })],
    }));
    assert.match(html, /bob/);
    assert.match(html, /Salmon Nigiri/);
    assert.match(html, /9 cards in hand/);
  });

  it('puts you first at the table', () => {
    const html = room(gameState({ players: [player('bob'), player('alice')] }));
    assert.ok(html.indexOf('alice (you)') < html.indexOf('>bob'));
  });

  it('finished: announces the winner with the final scores', () => {
    const html = room(gameState({
      status: 'finished',
      final_scores: { alice: 31, bob: 40 },
      players: [player('alice', { scores: [10, 10, 5] }), player('bob', { scores: [20, 10, 4] })],
    }));
    assert.match(html, /Game over/);
    assert.match(html, /bob won with 40 points/);
    assert.match(html, /Winner/);
  });

  it('finished: ties name everyone', () => {
    const html = room(gameState({ status: 'finished', final_scores: { alice: 20, bob: 20 } }));
    assert.match(html, /alice and bob won with 20 points/);
  });

  it('shows the previous round result', () => {
    const html = room(gameState({
      last_round: { number: 1, players: { alice: { played: [{ type: 'TempuraCard' }], score: 0 }, bob: { played: [], score: 5 } } },
    }));
    assert.match(html, /Round 1 result/);
    assert.match(html, /bob: 5 points/);
  });

  it('escapes hostile player names', () => {
    const html = room(gameState({ players: [player('alice'), player('<b onmouseover=x>bob</b>')] }));
    assert.doesNotMatch(html, /<b onmouseover/);
  });
});

describe('Scoreboard', () => {
  it('totals rounds while playing and shows dashes for rounds to come', () => {
    const html = render(<Scoreboard state={gameState({ players: [player('alice', { scores: [10, 5] }), player('bob', { scores: [3] })] })} />);
    assert.match(html, /<strong>15<\/strong>/);
    assert.match(html, /<strong>3<\/strong>/);
    assert.match(html, /–/);
  });

  it('uses the final scores (which include puddings) when the game is over', () => {
    const html = render(<Scoreboard state={gameState({
      status: 'finished',
      final_scores: { alice: 21, bob: 0 },
      players: [player('alice', { scores: [10, 5], pudding: 3 }), player('bob', { scores: [3], pudding: 0 })],
    })} />);
    assert.match(html, /<strong>21<\/strong>/);
    assert.match(html, /<strong>0<\/strong>/);
  });
});
