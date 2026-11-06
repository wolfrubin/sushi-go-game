"""Tests for the SuGo request handlers. These exercise the handlers directly
(no sockets), resetting the shared game dictionary between tests."""
import unittest
from server import sushi_handler
from server.sugo_request import SuGoRequest
from server.exceptions import (
    GameAlreadyExistsError,
    GameDoesNotExistError,
    GameInProgressError,
    InvalidRequestError,
    PlayerAlreadyJoinedError,
    SuGoError,
)
from sushi_go.deck import ChopsticksCard, TempuraCard, SashimiCard


def req(action, player='alice', game='g', body=''):
    return SuGoRequest('SuGo 1.0', action, game, player, body)


class HandlerTestCase(unittest.TestCase):

    def setUp(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()

    def tearDown(self):
        sushi_handler.GAME_DICT.underlying_dict.clear()

    def create(self, player='alice'):
        return sushi_handler.CreateGameHandler().handle(req('CREATE_GAME', player))

    def join(self, player):
        return sushi_handler.JoinGameHandler().handle(req('JOIN_GAME', player))

    def start(self, player='alice'):
        return sushi_handler.StartGameHandler().handle(req('START_GAME', player))

    def play(self, player, body):
        return sushi_handler.PlayCardHandler().handle(req('PLAY_CARD', player, body=body))

    def ready_game(self):
        self.create()
        self.join('bob')
        self.start()
        return sushi_handler.GAME_DICT['g']


class TestCreateAndJoin(HandlerTestCase):

    def test_create_game(self):
        self.assertEqual(self.create(), 'game created')
        engine = sushi_handler.GAME_DICT['g']
        self.assertTrue(engine.is_player_in('alice'))

    def test_create_duplicate_game(self):
        self.create()
        with self.assertRaises(GameAlreadyExistsError):
            self.create('bob')

    def test_join_game(self):
        self.create()
        self.assertEqual(self.join('bob'), 'joined game')
        self.assertEqual(sushi_handler.GAME_DICT['g'].number_of_players, 2)

    def test_join_missing_game(self):
        with self.assertRaises(GameDoesNotExistError):
            self.join('bob')

    def test_join_with_taken_name(self):
        self.create()
        with self.assertRaises(PlayerAlreadyJoinedError):
            self.join('alice')

    def test_errors_are_sugo_errors_with_messages(self):
        self.create()
        with self.assertRaises(SuGoError) as ctx:
            self.join('alice')
        self.assertIn('alice', ctx.exception.message)


class TestStartGame(HandlerTestCase):

    def test_start_game_deals_cards_once(self):
        engine = self.ready_game()
        self.assertTrue(engine.in_progress)
        self.assertEqual(len(engine.deck), 108 - 20)
        self.assertTrue(all(len(p.current_hand) == 10 for p in engine.players))

    def test_start_game_not_enough_players(self):
        self.create()
        with self.assertRaises(InvalidRequestError):
            self.start()
        self.assertFalse(sushi_handler.GAME_DICT['g'].in_progress)

    def test_start_game_twice(self):
        self.ready_game()
        with self.assertRaises(GameInProgressError):
            self.start()

    def test_start_missing_game(self):
        with self.assertRaises(GameDoesNotExistError):
            self.start()


class TestGameState(HandlerTestCase):

    def test_game_state_returns_only_requesting_players_hand(self):
        engine = self.ready_game()
        state = sushi_handler.GameStateHandler().handle(req('GAME_STATE', 'alice'))
        alice = [p for p in engine.players if p.name == 'alice'][0]
        self.assertEqual(state, str([alice.current_hand]))

    def test_game_state_missing_game(self):
        with self.assertRaises(GameDoesNotExistError):
            sushi_handler.GameStateHandler().handle(req('GAME_STATE'))


class TestPlayCard(HandlerTestCase):

    def test_play_card(self):
        engine = self.ready_game()
        self.assertEqual(self.play('alice', '0'), 'card played')
        alice = engine.players[0]
        self.assertEqual(len(alice.current_hand), 9)
        self.assertEqual(len(alice.played_cards), 1)

    def test_play_card_non_integer(self):
        self.ready_game()
        for body in ('abc', '', '1.5', '1,x'):
            with self.assertRaises(InvalidRequestError):
                self.play('alice', body)

    def test_play_card_out_of_range(self):
        self.ready_game()
        with self.assertRaises(InvalidRequestError):
            self.play('alice', '99')

    def test_play_card_twice_in_one_turn(self):
        self.ready_game()
        self.play('alice', '0')
        with self.assertRaises(InvalidRequestError):
            self.play('alice', '0')

    def test_play_card_unknown_player(self):
        self.ready_game()
        with self.assertRaises(InvalidRequestError):
            self.play('mallory', '0')

    def test_play_card_game_not_found(self):
        with self.assertRaises(GameDoesNotExistError):
            self.play('alice', '0')

    def test_play_two_cards_requires_chopsticks(self):
        engine = self.ready_game()
        with self.assertRaises(InvalidRequestError):
            self.play('alice', '0,1')
        self.assertEqual(len(engine.players[0].current_hand), 10)

    def test_play_two_cards_with_chopsticks(self):
        engine = self.ready_game()
        alice = engine.players[0]
        alice.played_cards = [ChopsticksCard()]
        # fixed cards so a random wasabi + nigiri draw can't merge on the table
        alice.current_hand[0:2] = [TempuraCard(), SashimiCard()]
        self.assertEqual(self.play('alice', '0,1'), 'card played')
        self.assertEqual(len(alice.played_cards), 2)
        self.assertEqual(len(alice.current_hand), 9)

    def test_play_two_cards_with_spaces_and_same_index(self):
        engine = self.ready_game()
        engine.players[0].played_cards = [ChopsticksCard()]
        self.assertEqual(self.play('alice', '0, 1'), 'card played')
        engine.players[0].can_play = True
        with self.assertRaises(InvalidRequestError):
            self.play('alice', '2,2')

    def test_play_three_indexes_rejected(self):
        self.ready_game()
        with self.assertRaises(InvalidRequestError):
            self.play('alice', '0,1,2')

    def test_both_players_playing_exchanges_hands(self):
        engine = self.ready_game()
        alice, bob = engine.players
        bob_hand = list(bob.current_hand)
        self.play('alice', '0')
        self.play('bob', '0')
        self.assertEqual(alice.current_hand, bob_hand[1:])


class TestGameDict(unittest.TestCase):

    def test_missing_key_raises_game_does_not_exist(self):
        with self.assertRaises(GameDoesNotExistError):
            sushi_handler.SuGoGameDict()['nope']

    def test_duplicate_key_raises(self):
        games = sushi_handler.SuGoGameDict()
        games['a'] = object()
        with self.assertRaises(GameAlreadyExistsError):
            games['a'] = object()
