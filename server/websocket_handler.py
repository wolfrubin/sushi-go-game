"""
This module is concenered with handling the http connection from the websocket.

Here we negotiate the websocket connection with the browser.

https://tools.ietf.org/html/rfc6455 for more information on websockets
"""
import json
import hashlib
import base64
from typing import List

from server.base_handler import BaseHandler


WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

class WebSocketHandler(BaseHandler):
    
    async def handle(self, body: List[bytes]):
        # Initialise handshake
        # Start connection loop

        print('Websocket handler')
        print('Constructing http object')
        request_dict = {k: v.strip() for k, v in [x.decode('utf-8').split(':', 1) for x in body[1:-2]]}
        print(json.dumps(request_dict, indent=4, default=str))
        ws_key = request_dict['Sec-WebSocket-Key'].encode('utf-8')
        response_key = base64.b64encode(hashlib.sha1(ws_key+WS_GUID).digest())
        response_list = [
            b'HTTP/1.1 101 Switching Protocols\r\n',
            b'Upgrade: websocket\r\n',
            b'Connection: Upgrade\r\n',
            b'Sec-WebSocket-Accept: ' + response_key + b'\r\n\r\n'
        ]
        print(json.dumps(response_list, indent=4, default=str))
        self.writer.writelines(response_list)
        await self.writer.drain()
