"""Tests for the WebSocket gateway. The core Gateway class is tested with fake
connections; a few tests then run it over real WebSockets when the optional
`websockets` package is installed."""
import asyncio
import json
import unittest

from server import gateway as gw
from server import sushi_handler
from sushi_go.deck import ChopsticksCard, SashimiCard, TempuraCard

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None


class FakeConn:
    """Stands in for a WebSocket: records everything the gateway sends."""

    def __init__(self, fail=False):
        self.messages = []
        self.fail = fail

    async def send(self, text):
        if self.fail:
            raise ConnectionError('closed')
        self.messages.append(json.loads(text))

    @property
    def replies(self):
        return [m for m in self.messages if 'event' not in m]

    @property
    def pushes(self):
        return [m for m in self.messages if m.get('event') == 'state']

    @property
    def last_reply(self):
        return self.replies[-1]

    @property
    def last_state(self):
        return self.pushes[-1]['state']


class GatewayTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()
        self.now = 1000.0
        self.gateway = gw.Gateway(clock=lambda: self.now)

    def tearDown(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()

    async def send(self, conn, **msg):
        await self.gateway.handle_message(conn, json.dumps(msg))
        return conn.last_reply

    async def start_two_player_game(self):
        alice, bob = FakeConn(), FakeConn()
        self.alice_token = (await self.send(alice, action='CREATE_GAME', game='g', player='alice'))['token']
        self.bob_token = (await self.send(bob, action='JOIN_GAME', game='g', player='bob'))['token']
        await self.send(alice, action='START_GAME', game='g', player='alice', token=self.alice_token)
        return alice, bob

    def engine(self, name='g'):
        return sushi_handler.GAME_DICT[name]


class TestMessageValidation(GatewayTestCase):

    async def error_for(self, raw):
        conn = FakeConn()
        await self.gateway.handle_message(conn, raw)
        reply = conn.last_reply
        self.assertFalse(reply['ok'])
        return reply['error']

    async def test_invalid_json(self):
        self.assertIn('JSON', await self.error_for('{nope'))

    async def test_not_an_object(self):
        for raw in ('[]', '3', '"x"', 'null'):
            self.assertIn('object', await self.error_for(raw))

    async def test_binary_message(self):
        self.assertIn('binary', await self.error_for(b'\x00\x01'))

    async def test_unknown_or_missing_action(self):
        for raw in ('{}', '{"action": "DANCE"}', '{"action": 5}', '{"action": "create_game"}'):
            self.assertIn('action', await self.error_for(raw))

    async def test_id_is_echoed_even_on_failure(self):
        conn = FakeConn()
        await self.gateway.handle_message(conn, json.dumps({'id': 'abc', 'action': 'DANCE'}))
        self.assertEqual(conn.last_reply['id'], 'abc')
        await self.gateway.handle_message(conn, json.dumps({'id': 7, 'action': 'LIST_GAMES'}))
        self.assertEqual(conn.last_reply['id'], 7)

    async def test_bad_id_types(self):
        for bad in (True, [], {}, 1.5, 'x' * 100):
            self.assertIn('id', await self.error_for(json.dumps({'id': bad, 'action': 'LIST_GAMES'})))

    async def test_name_validation(self):
        for game, player in (('', 'a'), ('g', ''), ('   ', 'a'), (None, 'a'), ('g', 5), ('g' * 33, 'a'),
                             ('g\r\nPLAY', 'a'), ('g', 'a\x00')):
            error = await self.error_for(json.dumps({'action': 'CREATE_GAME', 'game': game, 'player': player}))
            self.assertTrue(error)
        self.assertEqual(len(sushi_handler.GAME_DICT), 0)

    async def test_names_are_trimmed(self):
        conn = FakeConn()
        reply = await self.send(conn, action='CREATE_GAME', game='  g  ', player=' alice ')
        self.assertEqual((reply['game'], reply['player']), ('g', 'alice'))

    async def test_clean_body(self):
        self.assertEqual(gw.clean_body(None), '')
        self.assertEqual(gw.clean_body(3), '3')
        self.assertEqual(gw.clean_body([3, 5]), '3,5')
        self.assertEqual(gw.clean_body('3,5'), '3,5')
        for bad in (True, 1.5, {}, ['a'], [True], 'x' * 17):
            with self.assertRaises(gw.BadMessage):
                gw.clean_body(bad)

    async def test_rate_limit(self):
        conn = FakeConn()
        for _ in range(gw.RATE_LIMIT_MESSAGES):
            await self.send(conn, action='LIST_GAMES')
        self.assertTrue((await self.send(conn, action='LIST_GAMES')).get('ok') is False)
        self.assertIn('too many', conn.last_reply['error'])
        self.now += gw.RATE_LIMIT_WINDOW_SECONDS + 1
        self.assertTrue((await self.send(conn, action='LIST_GAMES'))['ok'])

    async def test_rate_limit_error_echoes_the_request_id(self):
        conn = FakeConn()
        for _ in range(gw.RATE_LIMIT_MESSAGES):
            await self.send(conn, action='LIST_GAMES')
        await self.gateway.handle_message(conn, json.dumps({'id': 77, 'action': 'LIST_GAMES'}))
        self.assertEqual((conn.last_reply['id'], conn.last_reply['ok']), (77, False))
        # unreadable messages are still refused, just without an id
        for raw in ('{nope', '[1]', b'\x00', json.dumps({'id': [1]})):
            await self.gateway.handle_message(conn, raw)
            self.assertEqual((conn.last_reply['id'], conn.last_reply['ok']), (None, False))


class TestLobbyAndTokens(GatewayTestCase):

    async def test_create_returns_token_and_pushes_state(self):
        conn = FakeConn()
        reply = await self.send(conn, action='CREATE_GAME', game='g', player='alice')
        self.assertTrue(reply['ok'])
        self.assertGreaterEqual(len(reply['token']), 16)
        self.assertEqual(conn.last_state['status'], 'lobby')
        self.assertEqual([p['name'] for p in conn.last_state['players']], ['alice'])

    async def test_failed_create_has_no_token(self):
        await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice')
        reply = await self.send(FakeConn(), action='CREATE_GAME', game='g', player='mallory')
        self.assertFalse(reply['ok'])
        self.assertNotIn('token', reply)
        self.assertIn('already exists', reply['error'])

    async def test_join_pushes_to_everyone_in_the_game(self):
        alice, bob = FakeConn(), FakeConn()
        await self.send(alice, action='CREATE_GAME', game='g', player='alice')
        await self.send(bob, action='JOIN_GAME', game='g', player='bob')
        for conn in (alice, bob):
            self.assertEqual([p['name'] for p in conn.last_state['players']], ['alice', 'bob'])
        self.assertEqual(alice.last_state['you'], 'alice')
        self.assertEqual(bob.last_state['you'], 'bob')

    async def test_tokens_are_unique_per_player(self):
        await self.start_two_player_game()
        self.assertNotEqual(self.alice_token, self.bob_token)

    async def test_cannot_steal_a_name(self):
        await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice')
        reply = await self.send(FakeConn(), action='JOIN_GAME', game='g', player='alice')
        self.assertFalse(reply['ok'])
        self.assertNotIn('token', reply)

    async def test_authenticated_actions_need_the_right_token(self):
        alice, bob = await self.start_two_player_game()
        for action in ('START_GAME', 'PLAY_CARD', 'GAME_STATE'):
            for token in (None, '', 'wrong', self.bob_token, 5):
                reply = await self.send(FakeConn(), action=action, game='g', player='alice', token=token, body=0)
                self.assertFalse(reply['ok'], (action, token))
                self.assertIn('invalid token', reply['error'])

    async def test_token_for_unknown_game_or_player(self):
        reply = await self.send(FakeConn(), action='GAME_STATE', game='nope', player='alice', token='x')
        self.assertFalse(reply['ok'])
        await self.start_two_player_game()
        reply = await self.send(FakeConn(), action='GAME_STATE', game='g', player='mallory', token=self.alice_token)
        self.assertFalse(reply['ok'])

    async def test_failed_auth_does_not_subscribe(self):
        await self.start_two_player_game()
        stranger = FakeConn()
        await self.send(stranger, action='GAME_STATE', game='g', player='alice', token='wrong')
        await self.gateway.broadcast('g')
        self.assertEqual(stranger.pushes, [])

    async def test_cannot_join_after_start_or_when_full(self):
        await self.start_two_player_game()
        reply = await self.send(FakeConn(), action='JOIN_GAME', game='g', player='carol')
        self.assertFalse(reply['ok'])
        self.assertIn('in progress', reply['error'])

    async def test_list_games(self):
        await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice')
        reply = await self.send(FakeConn(), action='LIST_GAMES')
        self.assertEqual(reply['games'], [{'name': 'g', 'players': ['alice'], 'status': 'lobby'}])

    async def test_list_games_needs_no_token(self):
        self.assertTrue((await self.send(FakeConn(), action='LIST_GAMES'))['ok'])

    async def test_game_limit(self):
        self.gateway.max_games = 2
        for name in ('a', 'b'):
            self.assertTrue((await self.send(FakeConn(), action='CREATE_GAME', game=name, player='p'))['ok'])
        reply = await self.send(FakeConn(), action='CREATE_GAME', game='c', player='p')
        self.assertFalse(reply['ok'])
        self.assertIn('too many games', reply['error'])
        self.assertEqual(len(sushi_handler.GAME_DICT), 2)


class TestPlaying(GatewayTestCase):

    async def test_start_pushes_personalised_hands(self):
        alice, bob = await self.start_two_player_game()
        a, b = alice.last_state, bob.last_state
        self.assertEqual((a['status'], b['status']), ('playing', 'playing'))
        self.assertEqual((len(a['hand']), len(b['hand'])), (10, 10))
        self.assertNotEqual(a['hand'], b['hand'])
        for state in (a, b):
            self.assertTrue(all('hand' not in p for p in state['players']))

    async def test_no_push_leaks_other_hands_or_tokens(self):
        alice, bob = await self.start_two_player_game()
        wire = json.dumps(alice.messages[-1])
        self.assertNotIn(self.bob_token, json.dumps(alice.messages))
        self.assertNotIn(self.alice_token, json.dumps(bob.messages))
        self.assertEqual(wire.count('"hand":'), 1)

    async def test_play_card_updates_everyone(self):
        alice, bob = await self.start_two_player_game()
        reply = await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        self.assertTrue(reply['ok'])
        for conn in (alice, bob):
            players = {p['name']: p for p in conn.last_state['players']}
            self.assertTrue(players['alice']['has_played'])
            self.assertFalse(players['bob']['has_played'])
        self.assertFalse(alice.last_state['can_play'])
        self.assertTrue(bob.last_state['can_play'])

    async def test_hands_rotate_after_both_play(self):
        alice, bob = await self.start_two_player_game()
        bob_hand = list(bob.last_state['hand'])
        await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        await self.send(bob, action='PLAY_CARD', game='g', player='bob', token=self.bob_token, body='0')
        self.assertEqual(alice.last_state['hand'], bob_hand[1:])
        self.assertTrue(alice.last_state['can_play'])

    async def test_invalid_plays_fail_without_broadcasting(self):
        alice, bob = await self.start_two_player_game()
        pushes_before = len(bob.pushes)
        for body in (99, 'abc', [1, 2, 3], '0,0'):
            reply = await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=body)
            self.assertFalse(reply['ok'], body)
        self.assertEqual(len(bob.pushes), pushes_before)

    async def test_playing_twice_in_a_turn(self):
        alice, _ = await self.start_two_player_game()
        await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        reply = await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        self.assertFalse(reply['ok'])

    async def test_chopsticks_with_list_body(self):
        alice, bob = await self.start_two_player_game()
        player = self.engine().players[0]
        player.played_cards = [ChopsticksCard()]
        player.current_hand[0:2] = [TempuraCard(), SashimiCard()]
        self.assertTrue(alice.last_state['can_use_chopsticks'] is False)  # stale push, state is re-read below
        reply = await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=[0, 1])
        self.assertTrue(reply['ok'])
        self.assertEqual([c['type'] for c in alice.last_state['players'][0]['played']], ['TempuraCard', 'SashimiCard'])
        self.assertEqual(len(alice.last_state['hand']), 9)

    async def test_full_game_ends_with_final_scores(self):
        alice, bob = await self.start_two_player_game()
        for _ in range(30):
            self.now += gw.RATE_LIMIT_WINDOW_SECONDS  # stay under the rate limit
            for conn, name, token in ((alice, 'alice', self.alice_token), (bob, 'bob', self.bob_token)):
                await self.send(conn, action='PLAY_CARD', game='g', player=name, token=token, body=0)
        state = alice.last_state
        self.assertEqual(state['status'], 'finished')
        self.assertEqual(set(state['final_scores']), {'alice', 'bob'})
        reply = await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        self.assertFalse(reply['ok'])

    async def test_games_are_isolated(self):
        alice, _ = await self.start_two_player_game()
        other = FakeConn()
        await self.send(other, action='CREATE_GAME', game='other', player='zed')
        pushes = len(other.pushes)
        await self.send(alice, action='PLAY_CARD', game='g', player='alice', token=self.alice_token, body=0)
        self.assertEqual(len(other.pushes), pushes)


class TestConnections(GatewayTestCase):

    async def test_reconnect_with_token_gets_state(self):
        alice, bob = await self.start_two_player_game()
        self.gateway.disconnect(alice)
        fresh = FakeConn()
        reply = await self.send(fresh, action='GAME_STATE', game='g', player='alice', token=self.alice_token)
        self.assertTrue(reply['ok'])
        self.assertEqual(reply['state']['you'], 'alice')
        self.assertEqual(len(reply['state']['hand']), 10)
        # and is subscribed again
        await self.send(bob, action='PLAY_CARD', game='g', player='bob', token=self.bob_token, body=0)
        self.assertTrue(fresh.last_state['players'][1]['has_played'])

    async def test_disconnect_stops_pushes(self):
        alice, bob = await self.start_two_player_game()
        self.gateway.disconnect(alice)
        before = len(alice.messages)
        await self.send(bob, action='PLAY_CARD', game='g', player='bob', token=self.bob_token, body=0)
        self.assertEqual(len(alice.messages), before)
        self.assertEqual(self.gateway.subscribers['g'], {bob: 'bob'})

    async def test_dead_connection_is_dropped_not_fatal(self):
        alice, bob = await self.start_two_player_game()
        dead = FakeConn(fail=True)
        self.gateway.subscribe(dead, 'g', 'alice')
        await self.send(bob, action='PLAY_CARD', game='g', player='bob', token=self.bob_token, body=0)
        self.assertNotIn(dead, self.gateway.subscribers['g'])
        self.assertTrue(alice.last_state['players'][1]['has_played'])

    async def test_disconnect_cleans_up_empty_games_and_rate_state(self):
        conn = FakeConn()
        await self.send(conn, action='CREATE_GAME', game='g', player='alice')
        self.gateway.disconnect(conn)
        self.assertEqual(self.gateway.subscribers, {})
        self.assertNotIn(conn, self.gateway.recent_messages)

    async def test_game_persists_after_everyone_disconnects(self):
        conn = FakeConn()
        token = (await self.send(conn, action='CREATE_GAME', game='g', player='alice'))['token']
        self.gateway.disconnect(conn)
        reply = await self.send(FakeConn(), action='GAME_STATE', game='g', player='alice', token=token)
        self.assertTrue(reply['ok'])


class TestSweep(GatewayTestCase):

    async def test_idle_games_are_removed_with_their_tokens(self):
        await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice')
        self.now += self.gateway.idle_seconds + 1
        self.assertEqual(self.gateway.sweep(), 1)
        self.assertEqual(len(sushi_handler.GAME_DICT), 0)
        self.assertEqual(self.gateway.tokens, {})
        self.assertEqual(self.gateway.subscribers, {})

    async def test_recent_activity_keeps_a_game(self):
        conn = FakeConn()
        token = (await self.send(conn, action='CREATE_GAME', game='g', player='alice'))['token']
        self.now += self.gateway.idle_seconds - 10
        await self.send(conn, action='GAME_STATE', game='g', player='alice', token=token)
        self.now += self.gateway.idle_seconds - 10
        self.assertEqual(self.gateway.sweep(), 0)
        self.assertIn('g', sushi_handler.GAME_DICT)

    async def test_games_made_elsewhere_age_out_too(self):
        sushi_handler.CreateGameHandler().handle(
            gw.SuGoRequest('SuGo 1.0', 'CREATE_GAME', 'tcp', 'alice', ''))
        self.assertEqual(self.gateway.sweep(), 0)  # first sighting starts the clock
        self.now += self.gateway.idle_seconds + 1
        self.assertEqual(self.gateway.sweep(), 1)

    async def test_a_removed_name_can_be_reused_with_a_fresh_token(self):
        old = (await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice'))['token']
        self.now += self.gateway.idle_seconds + 1
        self.gateway.sweep()
        new = (await self.send(FakeConn(), action='CREATE_GAME', game='g', player='alice'))['token']
        self.assertNotEqual(old, new)
        reply = await self.send(FakeConn(), action='GAME_STATE', game='g', player='alice', token=old)
        self.assertFalse(reply['ok'])


class TestArgs(unittest.TestCase):

    def test_defaults(self):
        args = gw.parse_args([])
        self.assertEqual((args.host, args.ws_port, args.tcp_port, args.no_tcp), ('127.0.0.1', 4137, 4136, False))
        self.assertEqual(args.origin, [])

    def test_options(self):
        args = gw.parse_args(['--ws-port', '9000', '--no-tcp', '--origin', 'https://a', '--origin', 'https://b',
                              '--idle-hours', '1'])
        self.assertEqual((args.ws_port, args.no_tcp, args.origin, args.idle_hours), (9000, True, ['https://a', 'https://b'], 1))


@unittest.skipIf(websockets is None, 'the websockets package is not installed')
class TestOverRealWebSockets(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()
        self.gateway = gw.Gateway()
        self.server = await gw.start_websocket_server(self.gateway, '127.0.0.1', 0, origins=['https://wolfrub.in'])
        self.uri = f'ws://127.0.0.1:{self.server.sockets[0].getsockname()[1]}'

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        sushi_handler.GAME_DICT.underlying_dict.clear()

    def connect(self, origin='https://wolfrub.in'):
        return websockets.connect(self.uri, origin=origin)

    async def call(self, ws, **msg):
        await ws.send(json.dumps(msg))
        while True:
            reply = json.loads(await asyncio.wait_for(ws.recv(), 5))
            if 'event' not in reply:
                return reply

    async def test_two_browsers_play_over_the_wire(self):
        async with self.connect() as alice, self.connect() as bob:
            created = await self.call(alice, id=1, action='CREATE_GAME', game='g', player='alice')
            joined = await self.call(bob, id=2, action='JOIN_GAME', game='g', player='bob')
            self.assertEqual((created['id'], joined['id']), (1, 2))
            started = await self.call(alice, action='START_GAME', game='g', player='alice', token=created['token'])
            self.assertTrue(started['ok'])
            # bob is pushed a personalised state without asking
            push = json.loads(await asyncio.wait_for(bob.recv(), 5))
            while push['state']['status'] != 'playing':
                push = json.loads(await asyncio.wait_for(bob.recv(), 5))
            self.assertEqual(push['state']['you'], 'bob')
            self.assertEqual(len(push['state']['hand']), 10)
            played = await self.call(bob, action='PLAY_CARD', game='g', player='bob', token=joined['token'], body=0)
            self.assertTrue(played['ok'])

    async def test_wrong_origin_is_refused(self):
        with self.assertRaises(websockets.exceptions.InvalidHandshake):
            async with self.connect(origin='https://evil.example'):
                pass

    async def test_client_without_origin_header_is_allowed(self):
        async with websockets.connect(self.uri) as ws:
            self.assertTrue((await self.call(ws, action='LIST_GAMES'))['ok'])

    async def test_oversized_message_closes_connection(self):
        async with self.connect() as ws:
            await ws.send('x' * (gw.MAX_MESSAGE_BYTES + 1))
            with self.assertRaises(websockets.exceptions.ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)

    async def test_binary_frame_is_rejected_politely(self):
        async with self.connect() as ws:
            await ws.send(b'\x00')
            reply = json.loads(await asyncio.wait_for(ws.recv(), 5))
            self.assertFalse(reply['ok'])
            self.assertTrue((await self.call(ws, action='LIST_GAMES'))['ok'])

    async def test_disconnect_is_cleaned_up(self):
        async with self.connect() as ws:
            await self.call(ws, action='CREATE_GAME', game='g', player='alice')
            self.assertEqual(len(self.gateway.subscribers['g']), 1)
        for _ in range(50):
            if not self.gateway.subscribers:
                break
            await asyncio.sleep(0.02)
        self.assertEqual(self.gateway.subscribers, {})


if __name__ == '__main__':
    unittest.main()
