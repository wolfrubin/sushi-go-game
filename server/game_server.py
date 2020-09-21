"""
Here I will try to implement the use the objects created to
make the game respond to an event loop running on a local socket.

This event loop runs as a separate process and has its own interface.

This will work as follows. Each event coming into the event loop
specifies which game and an action.

Games can be identified by a name (unique across all games)

An action is performed by a player.

A player is identified by a name (unique per game)

Actions current actions are as follows
CREATE_GAME
JOIN_GAME
START_GAME
PLAY_CARD
GAME_STATE

byte message (all utf-8) format:
ACTION_TYPE: CREATE_GAME/JOIN_GAME/START_GAME/PLAY_CARD/GAME_STATE
PARAMS:
    CREATE_GAME -> game_name, player_name
    JOIN_GAME -> game_name, player_name
    START_GAME -> game_name, player_name
    PLAY_CARD -> game_name, player_name, card_index
    GAME_STATE -> game_name, player_name
"""
import asyncio
import signal
import sys
import json

from sushi_go.game_engine import GameEngine


class SushiGoJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        print('HERE')
        print(obj)
        return str(obj)


CREATE_GAME = b'CREATE_GAME'
JOIN_GAME = b'JOIN_GAME'
START_GAME = b'START_GAME'
PLAY_CARD = b'PLAY_CARD'
GAME_STATE = b'GAME_STATE'

GAME_DICT = {}

STOP_BYTES = b'\n\n'

async def read_to_next(reader: asyncio.StreamReader):
    next_bytes = await reader.readuntil(STOP_BYTES)
    return next_bytes[:-2]


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_address = writer.get_extra_info('peername')
    print('client host {} port {} connected callback'.format(*client_address))
    action_name = await read_to_next(reader)
    print('action name {}'.format(action_name.decode('utf-8')))
    game_name = await read_to_next(reader)
    game_name = game_name.decode('utf-8')
    print('game named: {}'.format(game_name))
    player_name = await read_to_next(reader)
    player_name = player_name.decode('utf-8')
    print('player named: {}'.format(player_name))

    if action_name == CREATE_GAME:
        engine = GameEngine(game_name)
        engine.add_player_named(player_name)
        GAME_DICT[game_name] = engine
        writer.write(b'game started ')
    elif action_name == JOIN_GAME:
        engine = GAME_DICT[game_name]
        engine.add_player_named(player_name)
        writer.write(b'joined game')
    elif action_name == GAME_STATE:
        engine = GAME_DICT[game_name]
        hand_for_player =[x.current_hand for x in engine.players if x.name == player_name][0]
        writer.write(str(hand_for_player).encode('utf-8'))
    elif action_name == START_GAME:
        engine = GAME_DICT[game_name]
        engine.start_game()
        engine.start_round()
    elif action_name == PLAY_CARD:
        engine = GAME_DICT[game_name]
        index = await read_to_next(reader)
        index = int(index)
        print('playing index {}'.format(index))
        vals = engine.select_and_play(player_name, index)
        print(vals)
        bvals = json.dumps(vals, cls=SushiGoJSONEncoder).encode('utf-8')
        writer.write(bvals)
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
