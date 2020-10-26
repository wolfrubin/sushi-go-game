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
Body - Can be empty. Currently used to specifiy which card is played
    E.g. 0, 10


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
import signal
import sys

from server import sushi_handler
from server.sugo_request import SuGoRequest, SuGoResponse
from server.exceptions import SuGoError


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


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Client has connected to the SuGo server
    # Retrieve the rows to populate the request object
    sugo_request_vals = []
    for field in SuGoRequest._fields:
        field_bytes = await reader.readuntil(b'\r\n')
        field_string = field_bytes[:-2].decode('utf-8')
        sugo_request_vals.append(field_string)
    req = SuGoRequest(*sugo_request_vals)
    if req.protocol == 'SuGo 1.0':
        handler_class_name = make_handler_class_name(req.action_type)
        handler_class = getattr(sushi_handler, handler_class_name)
        handler = handler_class()
        try:
            response = handler.handle(req)
        except SuGoError as e:
            su_go_response = SuGoResponse(*[
                req.protocol,
                req.action_type,
                req.game_name,
                req.player,
                '0',
                e.message
            ])
        else:
            su_go_response = SuGoResponse(*[
                req.protocol,
                req.action_type,
                req.game_name,
                req.player,
                '1',
                response
            ])
        writer.write(response_to_bytes(su_go_response))
        await writer.drain()
        writer.close()


print('Starting sushi go server')

event_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()

factory = asyncio.start_server(client_connected, host='127.0.0.1', port=4136)
server = event_loop.run_until_complete(factory)


def shutdown():
    print('closing server')
    server.close()
    event_loop.stop()
    print('shutdown complete')
    sys.exit()

def signal_handler(sig, frame):
    print("signal {} caught".format(signal.Signals(sig).name))
    shutdown()

if __name__ == "__main__":
    print('installing signal handlers')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print('running server')
    event_loop.run_forever()
