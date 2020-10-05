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
import json
from typing import List

from server.base_handler import BaseHandler
from sushi_go.game_engine import GameEngine


class SushiGoJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        return str(obj)


CREATE_GAME = b'CREATE_GAME'
JOIN_GAME = b'JOIN_GAME'
START_GAME = b'START_GAME'
PLAY_CARD = b'PLAY_CARD'
GAME_STATE = b'GAME_STATE'

GAME_DICT = {}


class SushiHandler(BaseHandler):
    
    async def handle(self, body: List[bytes]):
        print('Sushi Handler')
        action_name = body[1]
        print('action name {}'.format(action_name.decode('utf-8')))
        game_name = body[2]
        game_name = game_name.decode('utf-8')
        print('game named: {}'.format(game_name))
        player_name = body[3]
        player_name = player_name.decode('utf-8')
        print('player named: {}'.format(player_name))

        if action_name == CREATE_GAME:
            engine = GameEngine(game_name)
            engine.add_player_named(player_name)
            GAME_DICT[game_name] = engine
            self.writer.write(b'game started ')
        elif action_name == JOIN_GAME:
            engine = GAME_DICT[game_name]
            engine.add_player_named(player_name)
            self.writer.write(b'joined game')
        elif action_name == GAME_STATE:
            engine = GAME_DICT[game_name]
            hand_for_player =[x.current_hand for x in engine.players if x.name == player_name][0]
            self.writer.write(str(hand_for_player).encode('utf-8'))
        elif action_name == START_GAME:
            engine = GAME_DICT[game_name]
            engine.start_game()
            engine.start_round()
        elif action_name == PLAY_CARD:
            engine = GAME_DICT[game_name]
            index = int(body[4])
            index = int(index)
            print('playing index {}'.format(index))
            vals = engine.select_and_play(player_name, index)
            print(vals)
            bvals = json.dumps(vals, cls=SushiGoJSONEncoder).encode('utf-8')
            self.writer.write(bvals)
        await self.writer.drain()
        self.writer.close()