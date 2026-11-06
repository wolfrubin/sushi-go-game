"""
This module is for the game server.

The game server needs to negotiate connections and pass the readers and writers
to the handler objects.

The sushi go game server handles request using the SuGo protocol.

The SuGo protocol is quite closely modelled around HTTP

A SuGo request looks like the following

HEADER
Protocol - Protocol name with version
    E.g. SuGo 1.0. (Casing important)
Action Type - Action you are attempting to perform
    E.g. CREATE_GAME (Upper case)
Game Name - The name of the game you are performing the operation on
    E.g. fun_and_descriptive_name
Player - The name of the player performing the action
    E.g. christian

BODY
Body - Can be empty. Currently used to specifiy which card is played.
    Two comma separated indexes play two cards using chopsticks
    E.g. 0, 10, 3,5


A SuGo response looks like the following

HEADER
Protocol - Protocol name with version
    E.g. SuGo 1.0 (Casing important)
Action Type - The action from the original request
    E.g. CREATE_GAME (Upper case)
Game Name - The name of the game you are performing the operation on
    E.g. fun_and_descriptive_name
Player - The name of the player performing the action
    E.g. christian
Status
    E.g. 1 or 0 representing SUCCESS/FAILURE

BODY
Body
    E.g. JSON. For FAILURE codes this response follows the format
    {failure_detail: descriptive reason why the request failed}

"""
import asyncio
import logging
import signal
from typing import Optional

from server import sushi_handler
from server.sugo_request import SuGoRequest, SuGoResponse
from server.exceptions import SuGoError, InvalidRequestError


logger = logging.getLogger(__name__)

PROTOCOL = 'SuGo 1.0'
HOST = '127.0.0.1'
PORT = 4136

FAILURE = '0'
SUCCESS = '1'


def make_handler_class_name(action_name: str):
    final_string_list = []
    next_to_upper = True
    for idx, char in enumerate(action_name):
        if char == '_':
            next_to_upper = True
            continue
        elif next_to_upper:
            final_string_list.append(char.upper())
            next_to_upper = False
        else:
            final_string_list.append(char.lower())
    return ''.join(final_string_list) + 'Handler'


def response_to_bytes(response: SuGoResponse):
    byte_list = b''
    for field in response:
        byte_list = byte_list + field.encode('utf-8') + b'\r\n'
    byte_list = byte_list + b'\r\n'
    return byte_list


def build_response(req: SuGoRequest, status: str, body: str) -> SuGoResponse:
    return SuGoResponse(req.protocol, req.action_type, req.game_name, req.player, status, body)


def dispatch(req: SuGoRequest) -> SuGoResponse:
    """
    Run a request through the matching handler and build the response.
    Expected failures (SuGoError) become FAILURE responses. This does no I/O
    so it can be tested without a socket.
    """
    handler_class = getattr(sushi_handler, make_handler_class_name(req.action_type), None)
    try:
        if handler_class is None:
            raise InvalidRequestError(f"unknown action \"{req.action_type}\"")
        return build_response(req, SUCCESS, handler_class().handle(req))
    except SuGoError as e:
        return build_response(req, FAILURE, e.message)
    except Exception:
        logger.exception("Unhandled error handling %s", req.action_type)
        return build_response(req, FAILURE, "Internal server error")


async def read_request(reader: asyncio.StreamReader) -> Optional[SuGoRequest]:
    """
    Read one request from the client. Returns None if the client hangs up
    part way through or sends bytes that are not valid utf-8.
    """
    values = []
    try:
        for _ in SuGoRequest._fields:
            field_bytes = await reader.readuntil(b'\r\n')
            values.append(field_bytes[:-2].decode('utf-8'))
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, UnicodeDecodeError):
        return None
    return SuGoRequest(*values)


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Client has connected to the SuGo server. Requests for any other
    # protocol are dropped without a response.
    try:
        req = await read_request(reader)
        if req is not None and req.protocol == PROTOCOL:
            writer.write(response_to_bytes(dispatch(req)))
            await writer.drain()
    finally:
        writer.close()


async def start_server(host: str = HOST, port: int = PORT) -> asyncio.AbstractServer:
    """Start listening. Pass port=0 to let the OS pick a free port."""
    return await asyncio.start_server(client_connected, host=host, port=port)


async def serve(host: str = HOST, port: int = PORT):
    server = await start_server(host, port)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    print(f'running server on {host}:{port}')
    await stop.wait()
    print('closing server')
    server.close()
    await server.wait_closed()
    print('shutdown complete')


def main():
    print('Starting sushi go server')
    asyncio.run(serve())


if __name__ == "__main__":
    main()
