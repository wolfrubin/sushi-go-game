"""
This module is for the game server.

The game server needs to negotiate connections and pass the readers and writers
to the handler objects.

There are two main handlers.

WebSocketHandler
    This is responsible for negotiating the websocket connection and allowing the
    browser (or other websocket interface client) to initiate a connection and start
    interfacing with the SushiHandler
SushiHandler
    This is the handler responsible for providing the gaming interface, for further
    details see the sushi_handler.py module
"""
import asyncio
import signal
import sys

from server.sushi_handler import SushiHandler
from server.websocket_handler import WebSocketHandler


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_address = writer.get_extra_info('peername')
    print('client host {} port {} connected callback'.format(*client_address))
    print('handshake determination')
    body = await reader.readuntil(b'\r\n\r\n')
    body = body.split(b'\r\n')
    if body[0].decode('utf-8') == 'sushigo':
        print('sushi go handler')
        handler = SushiHandler(reader, writer)
        await handler.handle(body)
    else:
        handler = WebSocketHandler(reader, writer)
        await handler.handle(body)


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
