import unittest
from main import GameEngine
from player import Player

"""
Here we test the core game engine. This class serves as the main access
point to interact with the game. When the time comes to make an API on
top of the game. This should be the main object interacted with.

Other than the Player class, everything else should remain hidden behind
the game engine class.
"""

class TestGameEngine(unittest.TestCase):
    
    def setUp(self):
        self.game_engine = GameEngine()
        self.player_one = self.game_engine.add_player()
        self.player_two = self.game_engine.add_player()
        
    def test_remove_player_start_game(self):
        """
        So we can't start the game when there aren't enough players.
        """
        self.game_engine.remove_player(self.player_one)

        self.assertEqual(self.game_engine.number_of_players(), 1)

        with self.assertRaises(Exception) as context:
            self.game_engine.start_game()

            self.assertTrue('Incorrect number of players' in context)

    def test_remove_player_failure(self):
        """
        We should not be able to remove a player that doesn't exist.
        """
        player_three = Player()

        with self.assertRaises(ValueError) as context:
            self.game_engine.remove_player(player_three)
            self.assertTrue('not in list' in context)

    def test_player_hands(self):
        """
        We need to make sure the correct number of players are in the
        game and that we have the correct number of cards per player.
        We also need to make sure that the hands have been assigned.
        """
        self.assertEqual(self.game_engine.number_of_players(), 2)

        self.game_engine.start_game()

        self.assertEqual(self.game_engine.cards_per_player, 10)
        self.assertNotEqual(self.player_one.current_hand, None)
        self.assertNotEqual(self.player_two.current_hand, None)
        self.assertEqual(len(self.player_one.current_hand), 10)

    def test_play_card(self):
        """
        We need to initialise the game then select a card to play.
        Then verify the card is moved to the played_cards hand.
        """
        self.game_engine.start_game()
        
        card = self.player_one.current_hand[0]
        self.game_engine.play_card(self.player_one, card)

        self.assertEqual(len(self.player_one.current_hand), 9)
        self.assertEqual(len(self.player_one.played_cards), 1)

    def test_players_ready(self):
        """
        Here we test the player ready functionality.
        Only once each player is ready to play their next card
        we allow the game to proceed and exchange hands.
        TODO. Verify that the exchange_hands method is called.
        """
        self.game_engine.start_game()

        card_p1 = self.player_one.current_hand[0]
        card_p2 = self.player_two.current_hand[1]

        self.game_engine.play_card(self.player_one, card_p1)
        self.assertEqual(self.game_engine.are_players_ready_next_card(), False)

        self.game_engine.play_card(self.player_two, card_p2)
        self.assertEqual(self.game_engine.are_players_ready_next_card(), True)

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
        player_three = self.game_engine.add_player()
        player_four = self.game_engine.add_player()
        player_five = self.game_engine.add_player()

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
        player_three = self.game_engine.add_player()
        player_four = self.game_engine.add_player()

        self.game_engine.hand_exchange_order = [player_three, player_four, self.player_one, self.player_two]
        
        self.game_engine.start_game()

        p1_hand = self.player_one.current_hand
        p4_hand = player_four.current_hand

        self.game_engine.exchange_hands()

        self.assertEqual(player_four.current_hand, p1_hand)

    def test_exchange_hands_twice(self):
        """
        We test the the hand exchanging mechanism works twice
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

    def test_exchange_is_ready_reset(self):
        """
        We test that once the is_ready flag is properly reset once 
        hands have been exchanged between players.
        """
        self.game_engine.start_game()

        self.game_engine.play_card(self.player_one, self.player_one.current_hand[0])
        self.assertEqual(self.player_one.is_ready, True)
        self.assertEqual(self.player_two.is_ready, False)
        self.game_engine.try_exchange_hands()

        self.game_engine.play_card(self.player_two, self.player_two.current_hand[0])
        self.assertEqual(self.player_two.is_ready, True)
        self.game_engine.try_exchange_hands()

        self.assertEqual(self.game_engine.are_players_ready_next_card(), False)

    def test_start_game_hand_size(self):
        # A little unnecessary to test
        self.game_engine.calc_card_per_player(2)
        self.assertEqual(self.game_engine.cards_per_player, 10)

        self.game_engine.calc_card_per_player(3)
        self.assertEqual(self.game_engine.cards_per_player, 9)

        self.game_engine.calc_card_per_player(4)
        self.assertEqual(self.game_engine.cards_per_player, 8)

        self.game_engine.calc_card_per_player(5)
        self.assertEqual(self.game_engine.cards_per_player, 7)



if __name__ == '__main__':
    unittest.main()