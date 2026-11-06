import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Col, Row } from 'react-bootstrap';
import { playBody, winners } from '../../lib/cards';
import type { GameState } from '../../lib/protocol';
import { CardFace } from './CardFace';
import { Scoreboard } from './Scoreboard';

interface GameRoomProps {
  state: GameState;
  onStart: () => Promise<void>;
  onPlay: (body: number | number[]) => Promise<void>;
  onLeave: () => void;
}

export function GameRoom({ state, onStart, onPlay, onLeave }: GameRoomProps) {
  const [selected, setSelected] = useState<number[]>([]);
  const [chopsticks, setChopsticks] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // A new turn (or a fresh hand) clears any half made choice
  useEffect(() => {
    setSelected([]);
    setChopsticks(false);
  }, [state.hand.length, state.round]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const needed = chopsticks ? 2 : 1;
  const toggle = (index: number) =>
    setSelected((current) => {
      if (current.includes(index)) return current.filter((i) => i !== index);
      const next = [...current, index];
      return next.length > needed ? next.slice(next.length - needed) : next;
    });

  const waitingOn = state.players.filter((p) => !p.has_played).map((p) => p.name);
  const me = state.players.find((p) => p.name === state.you);
  const ordered = [me, ...state.players.filter((p) => p.name !== state.you)].filter(Boolean);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="h4 mb-0">
          {state.game}
          {state.status === 'playing' && <small className="text-body-secondary"> · Round {state.round} of {state.max_rounds}</small>}
        </h2>
        <Button variant="outline-secondary" size="sm" onClick={onLeave}>Leave game</Button>
      </div>
      {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}

      {state.status === 'lobby' && (
        <Card body>
          <h3 className="h5">Waiting for players ({state.players.length}/5)</h3>
          <ul>{state.players.map((p) => <li key={p.name}>{p.name}{p.name === state.you ? ' (you)' : ''}</li>)}</ul>
          <p className="text-body-secondary">Others can join from the games list. You need at least 2 players.</p>
          <Button disabled={busy || state.players.length < 2} onClick={() => run(onStart)}>Start game</Button>
        </Card>
      )}

      {state.status === 'finished' && state.final_scores && (
        <Alert variant="success">
          <Alert.Heading as="h3" className="h5">Game over</Alert.Heading>
          {winners(state.final_scores).join(' and ')} won with {Math.max(...Object.values(state.final_scores))} points.
        </Alert>
      )}

      {state.status !== 'lobby' && (
        <>
          <Row className="g-3 mb-4">
            {ordered.map((player) => (
              <Col key={player!.name} md={ordered.length > 2 ? 6 : 12}>
                <Card className="h-100">
                  <Card.Header className="d-flex justify-content-between">
                    <span>{player!.name}{player!.name === state.you ? ' (you)' : ''}</span>
                    <span className="text-body-secondary small">
                      {state.status === 'playing' && `${player!.hand_size} cards in hand · `}
                      {player!.has_played ? 'played ✔' : state.status === 'playing' ? 'choosing…' : ''}
                    </span>
                  </Card.Header>
                  <Card.Body className="sg-table">
                    {player!.played.length === 0
                      ? <span className="text-body-secondary small">Nothing played yet this round</span>
                      : player!.played.map((card, i) => <CardFace key={i} card={card} small />)}
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {state.status === 'playing' && (
            <Card body className="mb-4">
              <div className="d-flex justify-content-between align-items-center mb-2" aria-live="polite">
                <h3 className="h5 mb-0">Your hand</h3>
                <span className="small text-body-secondary">
                  {state.can_play ? 'Your turn: pick a card' : `Waiting for ${waitingOn.join(', ')}…`}
                </span>
              </div>
              <div className="sg-hand">
                {state.hand.map((card, index) => (
                  <CardFace
                    key={index}
                    card={card}
                    selected={selected.includes(index)}
                    disabled={!state.can_play || busy}
                    onClick={() => toggle(index)}
                  />
                ))}
              </div>
              <div className="d-flex gap-2 mt-3 align-items-center flex-wrap">
                <Button
                  disabled={!state.can_play || busy || selected.length !== needed}
                  onClick={() => run(() => onPlay(playBody(selected)))}
                >
                  {chopsticks ? 'Play two cards' : 'Play card'}
                </Button>
                {state.can_use_chopsticks && (
                  <Button
                    variant={chopsticks ? 'warning' : 'outline-warning'}
                    aria-pressed={chopsticks}
                    onClick={() => { setChopsticks(!chopsticks); setSelected([]); }}
                  >
                    🥢 Use chopsticks
                  </Button>
                )}
              </div>
            </Card>
          )}
        </>
      )}

      {state.status !== 'lobby' && (
        <>
          <h3 className="h5">Scores</h3>
          <Scoreboard state={state} />
        </>
      )}

      {state.last_round && state.status !== 'lobby' && (
        <details className="mt-3">
          <summary>Round {state.last_round.number} result</summary>
          <ul className="mt-2">
            {Object.entries(state.last_round.players).map(([name, result]) => (
              <li key={name}>{name}: {result.score} points ({result.played.length} cards)</li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}
