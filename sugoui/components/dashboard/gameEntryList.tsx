import React, { useEffect } from 'react';
import { CardDeck, Col, Row } from 'react-bootstrap';
import { SushiGame } from '../../interfaces';
import { CreateGameDialogue } from './createGameDialogue';
import { GameTitleCard } from './gameTitleCard';

interface GameEntryListProps {
  games: SushiGame[];
  socket: WebSocket;
}

export function GameEntryList(props: GameEntryListProps) {
  useEffect(() => {
    if (props.socket) {
      if (props.socket.readyState == props.socket.OPEN) {
        props.socket.send('hi this is some data we are sending via a socket');
      }
    }
  })

  return <React.Fragment>
    <Row>
      <Col>
        <h2>All games listed here</h2>
      </Col>
    </Row>
    <Row>
      <Col>
        <CardDeck>
          {props.games?.map((game: SushiGame) => {
            return game.players.length !== 0 ? <GameTitleCard game={game} key={game.name} /> : null
          })}
        </CardDeck>
      </Col>
    </Row>
    <Row>
      <Col>
        <CreateGameDialogue />
      </Col>
    </Row>
  </React.Fragment>
}