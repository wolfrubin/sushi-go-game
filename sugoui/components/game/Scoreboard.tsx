import React from 'react';
import { Badge, Table } from 'react-bootstrap';
import { sum, winners } from '../../lib/cards';
import type { GameState } from '../../lib/protocol';

export function Scoreboard({ state }: { state: GameState }) {
  const rounds = Array.from({ length: state.max_rounds }, (_, i) => i);
  const champions = state.final_scores ? winners(state.final_scores) : [];
  return (
    <Table responsive size="sm" className="align-middle">
      <thead>
        <tr>
          <th scope="col">Player</th>
          {rounds.map((i) => <th key={i} scope="col" className="text-end">Round {i + 1}</th>)}
          <th scope="col" className="text-end">🍮</th>
          <th scope="col" className="text-end">Total</th>
        </tr>
      </thead>
      <tbody>
        {state.players.map((player) => (
          <tr key={player.name}>
            <th scope="row">
              {player.name}{player.name === state.you ? ' (you)' : ''}{' '}
              {champions.includes(player.name) && <Badge bg="warning" text="dark">Winner</Badge>}
            </th>
            {rounds.map((i) => <td key={i} className="text-end">{player.scores[i] ?? '–'}</td>)}
            <td className="text-end">{player.pudding}</td>
            <td className="text-end">
              <strong>{state.final_scores ? state.final_scores[player.name] : sum(player.scores)}</strong>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
