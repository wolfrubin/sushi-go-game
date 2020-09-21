"""Here we test the core game engine. This class serves as the main access
point to interact with the game. When the time comes to make an API on
top of the game. This should be the main object interacted with.

As much game logic as possible should remain hidden behind the game engine class.
"""
import unittest
import random
from sushi_go.game_engine import GameEngine
from sushi_go.player import Player


class TestGameEngine(unittest.TestCase):
    
    def setUp(self):
        self.game_engine = GameEngine('testname')
        self.game_engine.add_player_named('Test one')
        self.game_engine.add_player_named('Test two')

        self.player_one = self.game_engine.players[0]
        self.player_two = self.game_engine.players[1]
        
    def test_start_game_in_progress(self):
        """
        When the game has already been started it can't be started again.
        """
        self.game_engine.start_game()

        with self.assertRaises(Exception) as context:
            self.game_engine.start_game()

            self.assertTrue('Game in progress' in context)

    def test_remove_player_start_game(self):
        """
        So we can't start the game when there aren't enough players.
        """
        self.game_engine.remove_player(self.player_one)

        self.assertEqual(self.game_engine.number_of_players, 1)

        with self.assertRaises(Exception) as context:
            self.game_engine.start_game()

            self.assertTrue('Incorrect number of players' in context)

    def test_remove_player_failure(self):
        """
        We should not be able to remove a player that doesn't exist.
        """
        player_three = Player("Foo")

        with self.assertRaises(ValueError) as context:
            self.game_engine.remove_player(player_three)
            self.assertTrue('not in list' in context)

    def test_player_hands(self):
        """
        We need to make sure the correct number of players are in the
        game and that we have the correct number of cards per player.
        We also need to make sure that the hands have been assigned.
        """
        self.assertEqual(self.game_engine.number_of_players, 2)

        self.game_engine.start_game()

        self.assertEqual(self.game_engine.cards_per_player, 10)
        self.assertIsNot(self.player_one.current_hand, None)
        self.assertIsNot(self.player_two.current_hand, None)
        self.assertEqual(len(self.player_one.current_hand), 10)

    def test_draw_too_many_random_cards(self):
        """
        Here we test that the draw_random_cards method draws the right
        number of cards and that it errors when we try and draw too many
        cards.
        """
        deck = self.game_engine.deck

        self.assertEqual(len(deck.draw_random_cards(3)), 3)

        with self.assertRaises(Exception) as context:
            deck.draw_random_cards(1000)
            self.assertTrue('Tried to withdraw too many cards' in context)

    def test_play_card(self):
        """
        We need to initialise the game then select a card to play.
        Then verify the card is moved to the played_cards hand.
        """
        self.game_engine.start_game()
        
        self.game_engine.select_and_play(self.player_one.name, 0)

        self.assertEqual(len(self.player_one.current_hand), 9)
        self.assertEqual(len(self.player_one.played_cards), 1)

    def test_players_ready(self):
        """
        Here we test the player ready functionality.
        Only once each player is ready to play their next card
        we allow the game to proceed and exchange hands.
        """
        self.game_engine.start_game()

        self.game_engine.select_and_play(self.player_one.name, 0)
        self.assertFalse(self.game_engine.are_players_ready_next_card())

        self.game_engine.select_and_play(self.player_two.name, 1)
        self.assertTrue(self.game_engine.are_players_ready_next_card())

    def test_exchange_hands(self):
        """
        We need to verify the exchange hands method works.
        Default is the same order the players are added to the game.
        [1,2] => [2,1]
        """
        self.game_engine.start_game()

        p1_hand = self.player_one.current_hand
        p2_hand = self.player_two.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(self.player_one.current_hand, p2_hand)
        self.assertEqual(self.player_two.current_hand, p1_hand)

    def test_exchange_hands_five_players(self):
        """
        We test exchanging five players hands.
        [1,2,3,4,5] => [2,3,4,5,1]
        """
        self.game_engine.add_player_named('Three')
        self.game_engine.add_player_named('Four')
        self.game_engine.add_player_named('Five')

        player_four = self.game_engine.players[3]
        player_five = self.game_engine.players[4]

        self.game_engine.start_game()

        p5_hand = player_five.current_hand
        p1_hand = self.player_one.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(player_four.current_hand, p5_hand)
        self.assertEqual(player_five.current_hand, p1_hand)

    def test_exchange_hands_non_default(self):
        """
        Here we test that the hands are exchanged properly when a non
        default order is set. [3,4,1,2] => [4,1,2,3].
        I.E. player_three's hand should go to player four.
        """
        self.game_engine.add_player_named('Three')
        self.game_engine.add_player_named('Four')

        player_three = self.game_engine.players[2]
        player_four = self.game_engine.players[3]

        self.game_engine.set_hand_exchange_order([player_three, player_four, self.player_one, self.player_two])
        
        self.game_engine.start_game()

        p1_hand = self.player_one.current_hand
        p4_hand = player_four.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(player_four.current_hand, p1_hand)

    def test_exchange_hands_twice(self):
        """
        We test the the hand exchanging mechanism works twice.
        """
        self.game_engine.start_game()

        p1_hand = self.player_one.current_hand
        p2_hand = self.player_two.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(self.player_one.current_hand, p2_hand)
        self.assertEqual(self.player_two.current_hand, p1_hand)

        p1_hand = self.player_one.current_hand
        p2_hand = self.player_two.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(self.player_one.current_hand, p2_hand)
        self.assertEqual(self.player_two.current_hand, p1_hand)

    def test_exchange_can_play_reset(self):
        """
        We test that once the can_play flag is properly reset once 
        hands have been exchanged between players.
        """
        self.game_engine.start_game()

        self.game_engine.select_and_play(self.player_one.name, 0)
        self.assertFalse(self.player_one.can_play)
        self.assertTrue(self.player_two.can_play)
        hands_exchanged = self.game_engine.try_exchange_hands()

        self.assertFalse(hands_exchanged)

        self.game_engine.select_and_play(self.player_two.name, 0)
        self.assertFalse(self.player_two.can_play)
        hands_exchanged = self.game_engine.try_exchange_hands()

        self.assertTrue(hands_exchanged)

        self.assertFalse(self.game_engine.are_players_ready_next_card())

    def test_is_game_complete(self):
        """
        Game is complete when we reach the maximum number
        of rounds.
        """
        self.assertFalse(self.game_engine.is_game_complete())
        self.game_engine.current_round = self.game_engine.max_rounds
        self.assertTrue(self.game_engine.is_game_complete())

    def test_is_round_complete(self):
        """
        A round is complete when all players have 0 cards
        left in their hand.
        """
        self.game_engine.start_game()
        self.assertFalse(self.game_engine.is_round_complete())
        self.player_one.current_hand = []
        self.player_two.current_hand = []
        self.assertTrue(self.game_engine.is_round_complete())

    def test_record_scores(self):
        """
        Once the round is complete, we give the scorer the
        players who examines each players played cards. The
        scores are recorded in the game_engine. The scores
        are stored in a dictionary whose keys should be the
        player objects and corresponding object, the score.
        """
        self.player_one.played_cards = self.game_engine.deck.draw_random_cards(5)
        self.player_two.played_cards = self.game_engine.deck.draw_random_cards(5)
        self.game_engine.record_scores()

        for player in self.game_engine.players:
            self.assertTrue(player in self.game_engine.scores.keys())
            self.assertIsNotNone(self.game_engine.scores[player])

    def test_end_current_round(self):
        """
        To end the current round we need to increment the
        current round number and then record the scores.
        """
        round_before = self.game_engine.current_round
        self.game_engine.end_current_round()
        self.assertEqual(self.game_engine.current_round, round_before+1)

    def test_start_game_hand_size(self):
        """
        Test that the correct number of cards per player is set
        """
        self.game_engine.calc_card_per_player(2)
        self.assertEqual(self.game_engine.cards_per_player, 10)

        self.game_engine.calc_card_per_player(3)
        self.assertEqual(self.game_engine.cards_per_player, 9)

        self.game_engine.calc_card_per_player(4)
        self.assertEqual(self.game_engine.cards_per_player, 8)

        self.game_engine.calc_card_per_player(5)
        self.assertEqual(self.game_engine.cards_per_player, 7)
