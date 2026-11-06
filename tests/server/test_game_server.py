"""Tests for the SuGo game server: request parsing, dispatching, response
encoding, and a few end to end conversations over a real local socket."""
import asyncio
import unittest
from unittest import mock

from server import game_server, sushi_handler
from server.sugo_request import SuGoRequest, SuGoResponse


def raw_request(action, game='g', player='alice', body='', protocol='SuGo 1.0'):
    return ''.join(f'{field}\r\n' for field in (protocol, action, game, player, body)).encode('utf-8')


def parse_response(data: bytes):
    """Split a response into its fields (the trailing blank line is dropped)."""
    return data.decode('utf-8').split('\r\n')[:-2]


class TestHandlerClassName(unittest.TestCase):

    def test_action_names(self):
        self.assertEqual(game_server.make_handler_class_name('CREATE_GAME'), 'CreateGameHandler')
        self.assertEqual(game_server.make_handler_class_name('JOIN_GAME'), 'JoinGameHandler')
        self.assertEqual(game_server.make_handler_class_name('START_GAME'), 'StartGameHandler')
        self.assertEqual(game_server.make_handler_class_name('PLAY_CARD'), 'PlayCardHandler')
        self.assertEqual(game_server.make_handler_class_name('GAME_STATE'), 'GameStateHandler')

    def test_edge_cases(self):
        self.assertEqual(game_server.make_handler_class_name('create_game'), 'CreateGameHandler')
        self.assertEqual(game_server.make_handler_class_name('X'), 'XHandler')
        self.assertEqual(game_server.make_handler_class_name(''), 'Handler')

    def test_every_documented_action_has_a_handler(self):
        for action in ('CREATE_GAME', 'JOIN_GAME', 'START_GAME', 'PLAY_CARD', 'GAME_STATE'):
            name = game_server.make_handler_class_name(action)
            self.assertTrue(hasattr(sushi_handler, name), name)


class TestResponseToBytes(unittest.TestCase):

    def test_encoding(self):
        response = SuGoResponse('SuGo 1.0', 'CREATE_GAME', 'g', 'alice', '1', 'game created')
        self.assertEqual(
            game_server.response_to_bytes(response),
            b'SuGo 1.0\r\nCREATE_GAME\r\ng\r\nalice\r\n1\r\ngame created\r\n\r\n')

    def test_utf8(self):
        response = SuGoResponse('SuGo 1.0', 'A', 'sushi 🍣', 'joão', '1', '')
        data = game_server.response_to_bytes(response)
        self.assertIn('sushi 🍣'.encode('utf-8'), data)
        self.assertIn('joão'.encode('utf-8'), data)


class DispatchTestCase(unittest.TestCase):

    def setUp(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()

    def tearDown(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()

    def dispatch(self, action, player='alice', body='', game='g'):
        return game_server.dispatch(SuGoRequest('SuGo 1.0', action, game, player, body))


class TestDispatch(DispatchTestCase):

    def test_success_response_echoes_request_fields(self):
        response = self.dispatch('CREATE_GAME')
        self.assertEqual(
            tuple(response), ('SuGo 1.0', 'CREATE_GAME', 'g', 'alice', '1', 'game created'))

    def test_expected_failure_gives_failure_status_and_message(self):
        self.dispatch('CREATE_GAME')
        response = self.dispatch('CREATE_GAME', player='bob')
        self.assertEqual(response.status, '0')
        self.assertIn('already exists', response.body)
        self.assertEqual(response.player, 'bob')

    def test_unknown_action(self):
        response = self.dispatch('DANCE')
        self.assertEqual(response.status, '0')
        self.assertIn('unknown action "DANCE"', response.body)

    def test_odd_action_names_are_rejected(self):
        for action in ('GAME_ENGINE', 'SU_GO_GAME_DICT', '__BUILTINS__', 'create game', ''):
            self.assertEqual(self.dispatch(action).status, '0', action)

    def test_unexpected_exception_becomes_failure_and_is_logged(self):
        with mock.patch.object(sushi_handler.CreateGameHandler, 'handle', side_effect=RuntimeError('boom')):
            with self.assertLogs('server.game_server', level='ERROR'):
                response = self.dispatch('CREATE_GAME')
        self.assertEqual(response.status, '0')
        self.assertEqual(response.body, 'Internal server error')
        self.assertNotIn('boom', response.body)

    def test_full_game_through_dispatch(self):
        self.assertEqual(self.dispatch('CREATE_GAME').status, '1')
        self.assertEqual(self.dispatch('JOIN_GAME', player='bob').status, '1')
        self.assertEqual(self.dispatch('START_GAME').status, '1')
        self.assertEqual(self.dispatch('PLAY_CARD', body='0').status, '1')
        state = self.dispatch('GAME_STATE')
        self.assertEqual(state.status, '1')
        self.assertTrue(state.body.startswith('[['))

    def test_bad_play_body_is_failure(self):
        self.dispatch('CREATE_GAME')
        self.dispatch('JOIN_GAME', player='bob')
        self.dispatch('START_GAME')
        self.assertEqual(self.dispatch('PLAY_CARD', body='nope').status, '0')


class TestReadRequest(unittest.IsolatedAsyncioTestCase):

    async def read(self, data: bytes):
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()
        return await game_server.read_request(reader)

    async def test_parses_all_fields(self):
        req = await self.read(raw_request('PLAY_CARD', body='3,5'))
        self.assertEqual(req, SuGoRequest('SuGo 1.0', 'PLAY_CARD', 'g', 'alice', '3,5'))

    async def test_empty_body(self):
        req = await self.read(raw_request('GAME_STATE'))
        self.assertEqual(req.body, '')

    async def test_truncated_request_returns_none(self):
        self.assertIsNone(await self.read(b'SuGo 1.0\r\nCREATE_GAME\r\n'))

    async def test_empty_connection_returns_none(self):
        self.assertIsNone(await self.read(b''))

    async def test_invalid_utf8_returns_none(self):
        self.assertIsNone(await self.read(b'SuGo 1.0\r\n\xff\xfe\r\ng\r\nalice\r\n\r\n'))


class TestOverSocket(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()
        self.server = await game_server.start_server('127.0.0.1', 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        sushi_handler.GAME_DICT.underlying_dict.clear()

    async def send(self, data: bytes) -> bytes:
        reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
        writer.write(data)
        await writer.drain()
        response = await asyncio.wait_for(reader.read(), timeout=5)
        writer.close()
        await writer.wait_closed()
        return response

    async def test_create_game(self):
        response = await self.send(raw_request('CREATE_GAME'))
        self.assertEqual(parse_response(response),
                         ['SuGo 1.0', 'CREATE_GAME', 'g', 'alice', '1', 'game created'])

    async def test_failure_over_the_wire(self):
        await self.send(raw_request('CREATE_GAME'))
        response = parse_response(await self.send(raw_request('CREATE_GAME', player='bob')))
        self.assertEqual(response[4], '0')
        self.assertIn('already exists', response[5])

    async def test_unknown_action_gets_response_and_closes(self):
        response = parse_response(await self.send(raw_request('DANCE')))
        self.assertEqual(response[4], '0')

    async def test_other_protocol_is_closed_without_response(self):
        self.assertEqual(await self.send(raw_request('CREATE_GAME', protocol='HTTP/1.1')), b'')
        self.assertEqual(len(sushi_handler.GAME_DICT.underlying_dict), 0)

    async def test_client_hanging_up_mid_request_does_not_break_server(self):
        reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
        writer.write(b'SuGo 1.0\r\nCREATE_GAME\r\n')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        response = parse_response(await self.send(raw_request('CREATE_GAME')))
        self.assertEqual(response[4], '1')

    async def test_play_a_turn_end_to_end(self):
        await self.send(raw_request('CREATE_GAME', player='alice'))
        await self.send(raw_request('JOIN_GAME', player='bob'))
        await self.send(raw_request('START_GAME', player='alice'))
        played = parse_response(await self.send(raw_request('PLAY_CARD', player='alice', body='0')))
        self.assertEqual(played[4:], ['1', 'card played'])
        again = parse_response(await self.send(raw_request('PLAY_CARD', player='alice', body='0')))
        self.assertEqual(again[4], '0')

    async def test_concurrent_clients(self):
        responses = await asyncio.gather(*[
            self.send(raw_request('CREATE_GAME', game=f'game{i}', player='p')) for i in range(10)
        ])
        self.assertTrue(all(parse_response(r)[4] == '1' for r in responses))
        self.assertEqual(len(sushi_handler.GAME_DICT.underlying_dict), 10)


class TestModuleIsSideEffectFree(unittest.TestCase):

    def test_importing_does_not_start_a_server(self):
        import importlib
        with mock.patch('asyncio.start_server') as start, mock.patch('asyncio.get_event_loop') as get_loop:
            importlib.reload(game_server)
        start.assert_not_called()
        get_loop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
