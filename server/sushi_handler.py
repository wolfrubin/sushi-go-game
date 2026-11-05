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
LIST_GAMES

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
from sushi_go.player import PlayerCannotPlayException
from server.sugo_request import SuGoRequest
from server.exceptions import (
    GameAlreadyExistsError,
    GameDoesNotExistError,
    GameInProgressError,
    InvalidRequestError,
    PlayerAlreadyJoinedError
)


CREATE_GAME = b'CREATE_GAME'
JOIN_GAME = b'JOIN_GAME'
START_GAME = b'START_GAME'
PLAY_CARD = b'PLAY_CARD'
GAME_STATE = b'GAME_STATE'
LIST_GAMES = b'LIST_GAMES'

MAX_PLAYERS = 5


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

    def __contains__(self, name):
        return name in self.underlying_dict

    def __len__(self):
        return len(self.underlying_dict)

    def items(self):
        return list(self.underlying_dict.items())

    def remove(self, name):
        self.underlying_dict.pop(name, None)


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
        if engine.in_progress:
            raise GameInProgressError(req.game_name)
        if engine.number_of_players >= MAX_PLAYERS:
            raise InvalidRequestError(f"game \"{req.game_name}\" is full ({MAX_PLAYERS} players)")
        try:
            engine.add_player_named(req.player)
        except Exception:
            raise PlayerAlreadyJoinedError(req.game_name, req.player)
        return 'joined game'

class GameStateHandler:
    """Returns JSON describing the game from the requesting player's point
    of view (see GameEngine.state_for)."""

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        if not engine.is_player_in(req.player):
            raise InvalidRequestError(f"\"{req.player}\" is not in game \"{req.game_name}\"")
        return json.dumps(engine.state_for(req.player))


class ListGamesHandler:
    """Returns JSON listing every game and who is in it."""

    def handle(self, req: SuGoRequest):
        return json.dumps([
            {
                "name": name,
                "players": [player.name for player in engine.players],
                "status": engine.status(),
            }
            for name, engine in GAME_DICT.items()
        ])

class StartGameHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        if engine.in_progress:
            raise GameInProgressError(req.game_name)
        try:
            engine.start_game()
        except Exception as e:
            raise InvalidRequestError(str(e))
        return 'game started'

class PlayCardHandler:

    def handle(self, req: SuGoRequest):
        engine = GAME_DICT[req.game_name]
        # Body is a single card index, or two comma separated indexes when
        # playing two cards with chopsticks e.g. "3" or "3,5"
        try:
            indexes = [int(part) for part in req.body.split(',')]
        except ValueError:
            raise InvalidRequestError(f"card index must be an integer, got \"{req.body}\"")
        if len(indexes) not in (1, 2):
            raise InvalidRequestError("play one card index, or two when using chopsticks")
        try:
            if len(indexes) == 1:
                engine.select_and_play(req.player, indexes[0])
            else:
                engine.select_and_play_two(req.player, *indexes)
        except (IndexError, PlayerCannotPlayException) as e:
            raise InvalidRequestError(f"cannot play card(s) {req.body}")
        except Exception as e:
            raise InvalidRequestError(str(e))
        return 'card played'
