import React from 'react';
import { Accordion, Button, Form, InputGroup } from 'react-bootstrap';

export function CreateGameDialogue() {
  return <Accordion>
    <Accordion.Item eventKey="0">
      <Accordion.Header>Create a game!</Accordion.Header>
      <Accordion.Body>
        <InputGroup size="sm" className="mb-3">
          <InputGroup.Text id="game-name-input">Game name: </InputGroup.Text>
          <Form.Control aria-label="Game name input" aria-describedby="game-name-input" />
          <Button variant="primary">Create</Button>
        </InputGroup>
      </Accordion.Body>
    </Accordion.Item>
  </Accordion>;
}
