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
from abc import ABC, abstractmethod
from typing import List

from sushi_go.game_engine import GameEngine
from server.sugo_request import SuGoRequest
from server.exceptions import (
    GameAlreadyExistsError,
    GameDoesNotExistError,
    GameInProgressError,
    PlayerAlreadyJoinedError
)


CREATE_GAME = b'CREATE_GAME'
JOIN_GAME = b'JOIN_GAME'
START_GAME = b'START_GAME'
PLAY_CARD = b'PLAY_CARD'
GAME_STATE = b'GAME_STATE'


class SuGoGameDict:
    
    def __init__(self):
        self.underlying_dict = {}

    def __getitem__(self, name):
        try:
            return self.underlying_dict[name]
        except KeyError:
            raise GameDoesNotExistError(name)

    def __setitem__(self, key, item):
        if key in self.underlying_dict:
            raise GameAlreadyExistsError(key)
        else:
            self.underlying_dict[key] = item


GAME_DICT = SuGoGameDict()


class CreateGameHandler:

    def handle(self, req: SuGoRequest):
        engine = GameEngine(req.game_name)
        engine.add_player_named(req.player)
        GAME_DICT[req.game_name] = engine
        return 'game created'


class JoinGameHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        try:
            engine.add_player_named(req.player)
        except Exception:
            raise PlayerAlreadyJoinedError(req.game_name, req.player)
        return 'joined game'

class GameStateHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        hand_for_player = [x.current_hand for x in engine.players if x.name == req.player]
        return str(hand_for_player)

class StartGameHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        try:
            engine.start_game()
        except Exception:
            raise GameInProgressError(req.game_name)
        engine.start_round()
        return 'game started'

class PlayCardHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        index = int(req.body)
        vals = engine.select_and_play(req.player, index)
        return 'card played'
