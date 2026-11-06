import React, { useState } from 'react';
import { Alert, Badge, Button, Card, Col, Form, ListGroup, Row } from 'react-bootstrap';
import type { GameListing } from '../../lib/protocol';

interface LobbyProps {
  games: GameListing[] | null;
  initialName: string;
  connected: boolean;
  onCreate: (game: string, player: string) => Promise<void>;
  onJoin: (game: string, player: string) => Promise<void>;
}

const STATUS_LABEL = { lobby: 'Waiting for players', playing: 'In progress', finished: 'Finished' } as const;

export function Lobby({ games, initialName, connected, onCreate, onJoin }: LobbyProps) {
  const [player, setPlayer] = useState(initialName);
  const [newGame, setNewGame] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

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

  const nameOk = player.trim().length > 0;
  const canAct = connected && nameOk && !busy;

  return (
    <Row className="g-4">
      <Col md={5}>
        <Card body>
          <Form
            onSubmit={(event) => {
              event.preventDefault();
              if (canAct && newGame.trim()) run(() => onCreate(newGame.trim(), player.trim()));
            }}
          >
            <Form.Group className="mb-3" controlId="player-name">
              <Form.Label>Your name</Form.Label>
              <Form.Control value={player} maxLength={32} onChange={(e) => setPlayer(e.target.value)} autoComplete="nickname" />
            </Form.Group>
            <Form.Group className="mb-3" controlId="game-name">
              <Form.Label>Start a new game</Form.Label>
              <Form.Control placeholder="Game name" value={newGame} maxLength={32} onChange={(e) => setNewGame(e.target.value)} />
            </Form.Group>
            <Button type="submit" disabled={!canAct || !newGame.trim()}>Create game</Button>
          </Form>
          {!nameOk && <p className="text-body-secondary small mt-3 mb-0">Enter your name to create or join a game.</p>}
        </Card>
      </Col>
      <Col md={7}>
        <h2 className="h4">Games</h2>
        {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
        {games === null ? (
          <p className="text-body-secondary">{connected ? 'Loading games…' : 'Waiting for the game server…'}</p>
        ) : games.length === 0 ? (
          <p className="text-body-secondary">No games yet. Create one to get started!</p>
        ) : (
          <ListGroup>
            {games.map((game) => (
              <ListGroup.Item key={game.name} className="d-flex justify-content-between align-items-center gap-3">
                <div>
                  <strong>{game.name}</strong>{' '}
                  <Badge bg={game.status === 'lobby' ? 'success' : 'secondary'}>{STATUS_LABEL[game.status]}</Badge>
                  <div className="small text-body-secondary">{game.players.join(', ')}</div>
                </div>
                {game.status === 'lobby' && game.players.length < 5 && (
                  <Button size="sm" disabled={!canAct} onClick={() => run(() => onJoin(game.name, player.trim()))}>
                    Join
                  </Button>
                )}
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </Col>
    </Row>
  );
}
