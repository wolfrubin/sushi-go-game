import React from 'react';
import { Badge, Card, Col, ListGroup, Row } from 'react-bootstrap';
import { Player, SushiGame } from "../../interfaces";


interface GameTitleCardProps {
    game: SushiGame
}

export function GameTitleCard(props: GameTitleCardProps) {
    return <Card style={{width:'12rem'}}>
        <Card.Header>Game Name: {props.game.name}</Card.Header>
        <ListGroup variant="flush">
            {props.game.players?.map((player: Player) => {
                return <ListGroup.Item key={player.name}>{player.name}</ListGroup.Item>
            })}
        </ListGroup>
    </Card>
}