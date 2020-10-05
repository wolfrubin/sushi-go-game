import React, { useEffect, useState } from 'react'
import { Col, Row } from 'react-bootstrap';
import Container from 'react-bootstrap/Container'
import { GameEntryList } from '../components/dashboard/gameEntryList';
import { PageTitle } from '../components/dashboard/pageTitle';


function HomePage() {

  const [socket, setSocket] = useState<WebSocket>();

  // useEffect(() => {
  //   const socket = new WebSocket("ws://localhost:4136");
  //   setSocket(socket)
  // }, [socket])

  return <React.Fragment>
    <div className='page-header navbar navbar-dark bg-primary'>
      Christian Wolf Rubin
    </div>
  <Container fluid>
    <Row>
      <Col>
        <PageTitle />
      </Col>
    </Row>
    <Row>
      <Col>
        <GameEntryList socket={socket} games={[
          { name: 'hello', players: [{ name: 'christian' }, { name: 'brandon' }] },
          { name: 'goodbye', players: [] },
          { name: 'third game', players: [{ name: 'christian' }, { name: 'wendy' }, { name: 'becca' }] }
        ]} />
      </Col>
    </Row>
  </Container>
  </React.Fragment>
}

export default HomePage
