import React, { useState } from 'react';
import { Accordion, Button, Card, Col, FormControl, InputGroup, Row } from 'react-bootstrap';

export function CreateGameDialogue() {
  const [openDialogue, setOpenDialogue] = useState(false);
  const toggleOpenDialogue = () => {
    setOpenDialogue(!openDialogue);
  }
  return <Accordion>
    <Card>
      <Accordion.Toggle as={Card.Header} eventKey="0">
        Create a game!
      </Accordion.Toggle>
      <Accordion.Collapse eventKey="0">
        <Card.Body>
          <InputGroup size="sm" className="mb-3">
            <InputGroup.Prepend>
              <InputGroup.Text id="game-name-input">Game name: </InputGroup.Text>
            </InputGroup.Prepend>
            <FormControl aria-label="Game name input" aria-describedby="game-name-input" />
            <InputGroup.Append>
              <Button variant="primary">Create</Button>
            </InputGroup.Append>
          </InputGroup>
        </Card.Body>
      </Accordion.Collapse>
    </Card>
  </Accordion>
}