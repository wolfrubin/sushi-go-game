"""
WebSocket gateway for browsers.

Browsers cannot speak the raw TCP SuGo protocol, so this exposes the same
handlers over a WebSocket carrying JSON. Run it with

    python -m server.gateway

It also starts the TCP server (unless --no-tcp) so both front doors share the
same in-memory games.

Client -> server messages
    {"id": 1, "action": "CREATE_GAME", "game": "fun", "player": "christian"}
    {"id": 2, "action": "JOIN_GAME",   "game": "fun", "player": "brandon"}
    {"id": 3, "action": "START_GAME",  "game": "fun", "player": "christian", "token": "..."}
    {"id": 4, "action": "PLAY_CARD",   "game": "fun", "player": "christian", "token": "...", "body": 3}
    {"id": 5, "action": "PLAY_CARD",   ..., "body": [3, 5]}        two cards, needs chopsticks
    {"id": 6, "action": "GAME_STATE",  "game": "fun", "player": "christian", "token": "..."}
    {"id": 7, "action": "LIST_GAMES"}

  * "id" is optional and echoed back so replies can be matched to requests.
  * CREATE_GAME / JOIN_GAME reply with a secret "token". It must be sent with
    every later action for that player, so nobody can act as someone else.
    GAME_STATE with the token also re-attaches a reconnecting client.

Server -> client messages
    reply:  {"id": 1, "ok": true,  "action": "...", "game": "...", "player": "...", ...}
            {"id": 1, "ok": false, "error": "why it failed"}
            CREATE_GAME / JOIN_GAME replies add "token", GAME_STATE adds "state",
            LIST_GAMES adds "games".
    push:   {"event": "state", "state": {...}}
            sent to every connected player of a game after any change, personalised
            so each player only sees their own hand. See GameEngine.state_for.
"""
import argparse
import asyncio
import hmac
import json
import logging
import secrets
import signal
import time
from collections import deque
from typing import Any, Dict, Optional, Tuple

from server import game_server, sushi_handler
from server.exceptions import GameDoesNotExistError
from server.sugo_request import SuGoRequest

logger = logging.getLogger(__name__)

HOST = '127.0.0.1'
WS_PORT = 4137

MAX_MESSAGE_BYTES = 4096
MAX_NAME_LENGTH = 32
MAX_BODY_LENGTH = 16
MAX_ID_LENGTH = 64
MAX_GAMES = 200
IDLE_SECONDS = 6 * 60 * 60
RATE_LIMIT_MESSAGES = 20
RATE_LIMIT_WINDOW_SECONDS = 10

ACTIONS = {'LIST_GAMES', 'CREATE_GAME', 'JOIN_GAME', 'START_GAME', 'PLAY_CARD', 'GAME_STATE'}
# Actions that must carry the token issued when the player created/joined
AUTHENTICATED_ACTIONS = {'START_GAME', 'PLAY_CARD', 'GAME_STATE'}
# Actions that change a game, so every player in it is sent fresh state
BROADCAST_ACTIONS = {'CREATE_GAME', 'JOIN_GAME', 'START_GAME', 'PLAY_CARD'}


class BadMessage(Exception):
    """The client sent something we refuse to process. msg_id is the client's
    request id, when we got far enough to read it, so the error can be matched
    to the request."""

    def __init__(self, text, msg_id=None):
        super().__init__(text)
        self.msg_id = msg_id


def clean_name(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise BadMessage(f'"{label}" must be a string')
    value = value.strip()
    if not value:
        raise BadMessage(f'"{label}" is required')
    if len(value) > MAX_NAME_LENGTH:
        raise BadMessage(f'"{label}" must be at most {MAX_NAME_LENGTH} characters')
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise BadMessage(f'"{label}" contains control characters')
    return value


def clean_body(value: Any) -> str:
    """Card indexes may arrive as 3, [3, 5] or "3,5"."""
    if value is None:
        return ''
    if isinstance(value, bool):
        raise BadMessage('"body" must be a number, a list of numbers or a string')
    if isinstance(value, int):
        value = str(value)
    elif isinstance(value, list):
        if not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
            raise BadMessage('"body" list must contain only numbers')
        value = ','.join(str(item) for item in value)
    if not isinstance(value, str):
        raise BadMessage('"body" must be a number, a list of numbers or a string')
    if len(value) > MAX_BODY_LENGTH:
        raise BadMessage('"body" is too long')
    return value


class Gateway:
    """Transport independent core. A "connection" is anything with an async
    send(str) method, which keeps this testable without sockets."""

    def __init__(self, clock=time.monotonic, max_games=MAX_GAMES, idle_seconds=IDLE_SECONDS):
        self.clock = clock
        self.max_games = max_games
        self.idle_seconds = idle_seconds
        self.tokens: Dict[Tuple[str, str], str] = {}
        self.subscribers: Dict[str, Dict[Any, str]] = {}
        self.activity: Dict[str, float] = {}
        self.recent_messages: Dict[Any, deque] = {}

    # ---- connection lifecycle -------------------------------------------

    def disconnect(self, conn):
        for game in list(self.subscribers):
            self.subscribers[game].pop(conn, None)
            if not self.subscribers[game]:
                del self.subscribers[game]
        self.recent_messages.pop(conn, None)

    def subscribe(self, conn, game: str, player: str):
        self.subscribers.setdefault(game, {})[conn] = player

    # ---- message handling -----------------------------------------------

    async def handle_message(self, conn, raw):
        msg_id = None
        try:
            try:
                self._check_rate(conn)
            except BadMessage as error:
                error.msg_id = self._peek_id(raw)  # so the client can match the error to its request
                raise
            msg = self._parse(raw)
            msg_id = msg['id']
            reply, game = self._process(conn, msg)
        except BadMessage as error:
            await self._send(conn, {'id': error.msg_id if error.msg_id is not None else msg_id,
                                    'ok': False, 'error': str(error)})
            return
        reply['id'] = msg_id
        await self._send(conn, reply)
        if game is not None and msg['action'] in BROADCAST_ACTIONS:
            await self.broadcast(game)

    def _check_rate(self, conn):
        now = self.clock()
        recent = self.recent_messages.setdefault(conn, deque())
        while recent and now - recent[0] > RATE_LIMIT_WINDOW_SECONDS:
            recent.popleft()
        if len(recent) >= RATE_LIMIT_MESSAGES:
            raise BadMessage('too many messages, slow down')
        recent.append(now)

    @staticmethod
    def _peek_id(raw):
        """Best effort read of the request id from a message we are not going to process."""
        try:
            msg_id = json.loads(raw).get('id')
        except (ValueError, TypeError, AttributeError):
            return None
        if isinstance(msg_id, bool) or not (
                isinstance(msg_id, int) or (isinstance(msg_id, str) and len(msg_id) <= MAX_ID_LENGTH)):
            return None
        return msg_id

    @staticmethod
    def _parse(raw) -> dict:
        if not isinstance(raw, str):
            raise BadMessage('binary messages are not supported')
        try:
            msg = json.loads(raw)
        except ValueError:
            raise BadMessage('message is not valid JSON')
        if not isinstance(msg, dict):
            raise BadMessage('message must be a JSON object')
        msg_id = msg.get('id')
        if isinstance(msg_id, bool) or not (
                msg_id is None or isinstance(msg_id, int)
                or (isinstance(msg_id, str) and len(msg_id) <= MAX_ID_LENGTH)):
            raise BadMessage('"id" must be a number or short string')
        msg['id'] = msg_id
        action = msg.get('action')
        if not isinstance(action, str) or action not in ACTIONS:
            raise BadMessage(f'"action" must be one of {sorted(ACTIONS)}', msg_id)
        return msg

    def _process(self, conn, msg: dict) -> Tuple[dict, Optional[str]]:
        action = msg['action']

        if action == 'LIST_GAMES':
            response = self._dispatch(action, '', '', '')
            return {'ok': True, 'action': action, 'games': json.loads(response.body)}, None

        game = clean_name(msg.get('game'), 'game')
        player = clean_name(msg.get('player'), 'player')
        body = clean_body(msg.get('body'))
        reply = {'action': action, 'game': game, 'player': player}

        if action == 'CREATE_GAME' and len(sushi_handler.GAME_DICT) >= self.max_games:
            return {**reply, 'ok': False, 'error': 'the server has too many games, try again later'}, None
        if action in AUTHENTICATED_ACTIONS:
            self._check_token(game, player, msg.get('token'))

        response = self._dispatch(action, game, player, body)
        if response.status != game_server.SUCCESS:
            return {**reply, 'ok': False, 'error': response.body}, None

        reply['ok'] = True
        if action in ('CREATE_GAME', 'JOIN_GAME'):
            reply['token'] = self._issue_token(game, player)
        if action == 'GAME_STATE':
            reply['state'] = json.loads(response.body)
        self.subscribe(conn, game, player)
        self.activity[game] = self.clock()
        return reply, game

    @staticmethod
    def _dispatch(action, game, player, body):
        return game_server.dispatch(SuGoRequest(game_server.PROTOCOL, action, game, player, body))

    # ---- tokens ----------------------------------------------------------

    def _issue_token(self, game: str, player: str) -> str:
        token = secrets.token_urlsafe(16)
        self.tokens[(game, player)] = token
        return token

    def _check_token(self, game: str, player: str, token: Any):
        expected = self.tokens.get((game, player))
        if expected is None or not isinstance(token, str) or not hmac.compare_digest(
                expected.encode('utf-8'), token.encode('utf-8')):
            raise BadMessage('invalid token for this player')

    # ---- pushing state ---------------------------------------------------

    async def broadcast(self, game: str):
        try:
            engine = sushi_handler.GAME_DICT[game]
        except GameDoesNotExistError:
            return

        async def push(conn, player):
            try:
                state = engine.state_for(player)
            except IndexError:
                return
            await self._send(conn, {'event': 'state', 'state': state})

        await asyncio.gather(*(push(conn, player) for conn, player in list(self.subscribers.get(game, {}).items())))

    async def _send(self, conn, payload: dict):
        try:
            await conn.send(json.dumps(payload))
        except Exception:
            logger.debug('dropping connection that failed to receive a message', exc_info=True)
            self.disconnect(conn)

    # ---- housekeeping ----------------------------------------------------

    def sweep(self) -> int:
        """Forget games nobody has touched for idle_seconds. Returns how many."""
        now = self.clock()
        removed = 0
        for name, _ in sushi_handler.GAME_DICT.items():
            last_seen = self.activity.setdefault(name, now)
            if now - last_seen > self.idle_seconds:
                sushi_handler.GAME_DICT.remove(name)
                self.activity.pop(name, None)
                self.subscribers.pop(name, None)
                for key in [key for key in self.tokens if key[0] == name]:
                    del self.tokens[key]
                removed += 1
        return removed


# ---- transport -----------------------------------------------------------

async def start_websocket_server(gateway: Gateway, host: str = HOST, port: int = WS_PORT, origins=None):
    """Listen for WebSocket clients. Pass port=0 to let the OS pick a port.
    If origins is given, browsers must come from one of them. Clients that
    send no Origin header (scripts, CLIs) are still allowed."""
    import websockets
    from websockets.exceptions import ConnectionClosed

    async def handler(websocket):
        try:
            async for raw in websocket:
                await gateway.handle_message(websocket, raw)
        except ConnectionClosed:
            pass  # a tab closing or a network drop is normal, not an error
        finally:
            gateway.disconnect(websocket)

    allowed = None if not origins else list(origins) + [None]
    return await websockets.serve(handler, host, port, max_size=MAX_MESSAGE_BYTES, origins=allowed)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Sushi Go WebSocket gateway')
    parser.add_argument('--host', default=HOST)
    parser.add_argument('--ws-port', type=int, default=WS_PORT)
    parser.add_argument('--tcp-port', type=int, default=game_server.PORT)
    parser.add_argument('--no-tcp', action='store_true', help='do not start the raw TCP SuGo server')
    parser.add_argument('--origin', action='append', default=[],
                        help='allowed browser Origin, e.g. https://wolfrub.in (repeatable)')
    parser.add_argument('--max-games', type=int, default=MAX_GAMES)
    parser.add_argument('--idle-hours', type=float, default=IDLE_SECONDS / 3600)
    return parser.parse_args(argv)


async def sweep_forever(gateway: Gateway, interval: float = 60):
    while True:
        await asyncio.sleep(interval)
        removed = gateway.sweep()
        if removed:
            logger.info('removed %d idle games', removed)


async def serve(args):
    gateway = Gateway(max_games=args.max_games, idle_seconds=args.idle_hours * 3600)
    ws_server = await start_websocket_server(gateway, args.host, args.ws_port, args.origin)
    tcp_server = None if args.no_tcp else await game_server.start_server(args.host, args.tcp_port)
    sweeper = asyncio.ensure_future(sweep_forever(gateway))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    print(f'websocket gateway on ws://{args.host}:{args.ws_port}')
    if tcp_server:
        print(f'tcp server on {args.host}:{args.tcp_port}')
    await stop.wait()

    print('shutting down')
    sweeper.cancel()
    ws_server.close()
    await ws_server.wait_closed()
    if tcp_server:
        tcp_server.close()
        await tcp_server.wait_closed()
    print('shutdown complete')


def main(argv=None):
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve(parse_args(argv)))


if __name__ == '__main__':
    main()
