import Head from 'next/head';
import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Container, Navbar } from 'react-bootstrap';
import { GameRoom } from '../components/game/GameRoom';
import { Lobby } from '../components/game/Lobby';
import type { GameListing, Session } from '../lib/protocol';
import { clearSession, loadPlayerName, loadSession, saveSession } from '../lib/session';
import { useSugo } from '../lib/useSugo';

const GAME_LIST_REFRESH_MS = 5000;

export default function HomePage() {
  const { client, status, state, sessionLost } = useSugo();
  const [session, setSession] = useState<Session | null>(null);
  const [games, setGames] = useState<GameListing[] | null>(null);
  const [initialName, setInitialName] = useState('');
  const [ready, setReady] = useState(false);

  // Browser only: pick up a saved session so a refresh puts you back in your game
  useEffect(() => {
    const saved = loadSession();
    setInitialName(loadPlayerName());
    if (saved) {
      setSession(saved);
      client.setSession(saved);
    }
    setReady(true);
  }, [client]);

  const leave = useCallback(() => {
    clearSession();
    setSession(null);
    client.setSession(null);
  }, [client]);

  useEffect(() => {
    if (sessionLost) leave();
  }, [sessionLost, leave]);

  // Keep the games list fresh while choosing a game
  useEffect(() => {
    if (session || status !== 'open') return;
    let cancelled = false;
    const refresh = () =>
      client.request('LIST_GAMES').then((reply) => { if (!cancelled) setGames(reply.games ?? []); }).catch(() => {});
    refresh();
    const timer = setInterval(refresh, GAME_LIST_REFRESH_MS);
    return () => { cancelled = true; clearInterval(timer); };
  }, [client, session, status]);

  const enter = async (action: 'CREATE_GAME' | 'JOIN_GAME', game: string, player: string) => {
    const reply = await client.request(action, { game, player });
    const next: Session = { game, player, token: reply.token as string };
    saveSession(next);
    setSession(next);
    client.setSession(next);
  };

  return (
    <>
      <Head>
        <title>Sushi Go!</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Navbar bg="primary" variant="dark" className="mb-4">
        <Container>
          <Navbar.Brand>🍣 Sushi Go!</Navbar.Brand>
        </Container>
      </Navbar>
      <Container className="pb-5">
        {ready && status !== 'open' && (
          <Alert variant="warning" role="status">
            {status === 'connecting' ? 'Connecting to the game server…' : 'Disconnected from the game server.'}
          </Alert>
        )}
        {ready && !session && (
          <Lobby
            games={games}
            initialName={initialName}
            connected={status === 'open'}
            onCreate={(game, player) => enter('CREATE_GAME', game, player)}
            onJoin={(game, player) => enter('JOIN_GAME', game, player)}
          />
        )}
        {session && !state && <p className="text-body-secondary">Rejoining {session.game}…</p>}
        {session && state && (
          <GameRoom
            state={state}
            onStart={async () => { await client.act('START_GAME'); }}
            onPlay={async (body) => { await client.act('PLAY_CARD', body); }}
            onLeave={leave}
          />
        )}
      </Container>
    </>
  );
}
