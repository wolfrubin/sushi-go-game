"""Here we test the core game engine. This class serves as the main access
point to interact with the game. When the time comes to make an API on
top of the game. This should be the main object interacted with.

As much game logic as possible should remain hidden behind the game engine class.
"""
import unittest
import random
from sushi_go.game_engine import GameEngine
from sushi_go.player import Player, PlayerCannotPlayException
from sushi_go.deck import PuddingCard, ChopsticksCard, TempuraCard, WasabiCard, SquidNigiriCard, CARD_TYPE_DISTRIBUTION


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

        # Once everyone has played, select_and_play exchanges the hands and
        # resets every player's can_play flag.
        self.game_engine.select_and_play(self.player_two.name, 1)
        self.assertTrue(self.player_one.can_play)
        self.assertTrue(self.player_two.can_play)

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

        # The second play triggers the exchange automatically and resets
        # can_play for everyone.
        self.game_engine.select_and_play(self.player_two.name, 0)
        self.assertTrue(self.player_one.can_play)
        self.assertTrue(self.player_two.can_play)
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
            self.assertTrue(player.name in self.game_engine.scores.keys())
            self.assertIsNotNone(self.game_engine.scores[player.name])

    def test_end_current_round(self):
        """
        To end the current round we need to increment the
        current round number and then record the scores.
        """
        self.game_engine.start_game()
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


    def test_game_complete_totals_scores_by_player_name(self):
        """
        Finishing the final round returns each player's total score.
        """
        self.game_engine.start_game()
        self.game_engine.current_round = self.game_engine.max_rounds - 1
        result = self.game_engine.end_current_round()
        self.assertEqual(set(result.keys()), {'Test one', 'Test two'})


    def test_deck_is_standard_108_cards(self):
        self.assertEqual(sum(CARD_TYPE_DISTRIBUTION.values()), 108)
        self.assertEqual(len(self.game_engine.deck), 108)

    def test_puddings_carry_over_between_rounds_and_score_at_end(self):
        self.game_engine.start_game()
        self.player_one.played_cards = [PuddingCard(), PuddingCard()]
        self.player_two.played_cards = [PuddingCard()]
        self.game_engine.end_current_round()
        self.assertEqual(self.player_one.pudding_count, 2)
        self.assertEqual(self.player_two.pudding_count, 1)
        # new round clears the table but keeps the pudding tally
        self.assertEqual(self.player_one.played_cards, [])

        self.game_engine.current_round = self.game_engine.max_rounds - 1
        self.player_one.played_cards = []
        self.player_two.played_cards = []
        totals = self.game_engine.end_current_round()
        self.assertEqual(totals['Test one'] - sum(self.game_engine.scores['Test one']), 6)
        self.assertEqual(totals['Test two'] - sum(self.game_engine.scores['Test two']), 0)

    def test_select_and_play_two_with_chopsticks(self):
        self.game_engine.start_game()
        chopsticks = ChopsticksCard()
        self.player_one.played_cards = [chopsticks]
        hand = self.player_one.current_hand
        first, second = hand[0], hand[1]

        self.game_engine.select_and_play_two(self.player_one.name, 0, 1)

        self.assertEqual(self.player_one.played_cards[-2:], [first, second])
        self.assertNotIn(chopsticks, self.player_one.played_cards)
        self.assertIn(chopsticks, self.player_one.current_hand)
        self.assertEqual(len(self.player_one.current_hand), 9)

    def test_select_and_play_two_requires_chopsticks(self):
        self.game_engine.start_game()
        with self.assertRaises(Exception):
            self.game_engine.select_and_play_two(self.player_one.name, 0, 1)

    def test_full_game_five_players_does_not_run_out_of_cards(self):
        engine = GameEngine('big')
        for name in 'abcde':
            engine.add_player_named(name)
        engine.start_game()
        result = None
        while result is None:
            for player in engine.players:
                result = engine.select_and_play(player.name, 0)
        self.assertEqual(set(result), set('abcde'))


class TestGameEngineFlow(unittest.TestCase):

    def make_engine(self, names=('a', 'b')):
        engine = GameEngine('flow')
        for name in names:
            engine.add_player_named(name)
        return engine

    def test_duplicate_player_name_rejected(self):
        engine = self.make_engine()
        with self.assertRaises(Exception):
            engine.add_player_named('a')
        self.assertEqual(engine.number_of_players, 2)

    def test_is_player_in(self):
        engine = self.make_engine()
        self.assertTrue(engine.is_player_in('a'))
        self.assertFalse(engine.is_player_in('zzz'))

    def test_start_game_player_count_limits(self):
        with self.assertRaises(Exception):
            self.make_engine(('a',)).start_game()
        with self.assertRaises(Exception):
            self.make_engine(tuple('abcdef')).start_game()
        for count in range(2, 6):
            engine = self.make_engine(tuple('abcde')[:count])
            engine.start_game()
            self.assertTrue(engine.in_progress)

    def test_start_game_deals_once(self):
        engine = self.make_engine()
        engine.start_game()
        self.assertEqual(len(engine.deck), 108 - 2 * 10)
        for player in engine.players:
            self.assertEqual(len(player.current_hand), 10)

    def test_hand_sizes_per_player_count(self):
        for count in range(2, 6):
            engine = self.make_engine(tuple('abcde')[:count])
            engine.start_game()
            for player in engine.players:
                self.assertEqual(len(player.current_hand), 12 - count)

    def test_mid_turn_play_does_not_exchange_or_end_round(self):
        engine = self.make_engine()
        engine.start_game()
        before = list(engine.players[1].current_hand)
        self.assertIsNone(engine.select_and_play('a', 0))
        self.assertEqual(engine.players[1].current_hand, before)

    def test_hands_rotate_after_everyone_plays(self):
        engine = self.make_engine(('a', 'b', 'c'))
        engine.start_game()
        a, b, c = engine.players
        a_hand, b_hand, c_hand = list(a.current_hand), list(b.current_hand), list(c.current_hand)
        a_card, b_card, c_card = a_hand[0], b_hand[0], c_hand[0]
        for player in (a, b, c):
            engine.select_and_play(player.name, 0)
        self.assertEqual(a.current_hand, b_hand[1:])
        self.assertEqual(b.current_hand, c_hand[1:])
        self.assertEqual(c.current_hand, a_hand[1:])
        self.assertEqual((a.played_cards, b.played_cards, c.played_cards), ([a_card], [b_card], [c_card]))
        self.assertTrue(all(p.can_play for p in engine.players))

    def test_player_cannot_play_twice_before_others(self):
        engine = self.make_engine()
        engine.start_game()
        engine.select_and_play('a', 0)
        with self.assertRaises(PlayerCannotPlayException):
            engine.select_and_play('a', 0)

    def test_unknown_player_or_bad_index(self):
        engine = self.make_engine()
        engine.start_game()
        with self.assertRaises(IndexError):
            engine.select_and_play('nobody', 0)
        with self.assertRaises(IndexError):
            engine.select_and_play('a', 99)

    def play_round(self, engine):
        result = None
        round_number = engine.current_round
        while engine.current_round == round_number:
            for player in engine.players:
                result = engine.select_and_play(player.name, 0)
        return result

    def test_round_end_scores_and_deals_next_round(self):
        engine = self.make_engine()
        engine.start_game()
        self.play_round(engine)
        self.assertEqual(engine.current_round, 1)
        self.assertEqual([len(v) for v in engine.scores.values()], [1, 1])
        for player in engine.players:
            self.assertEqual(player.played_cards, [])
            self.assertEqual(len(player.current_hand), 10)

    def test_full_game_records_three_rounds_and_totals(self):
        engine = self.make_engine()
        engine.start_game()
        totals = None
        for _ in range(engine.max_rounds):
            totals = self.play_round(engine)
        self.assertEqual(engine.current_round, 3)
        self.assertEqual({n: len(v) for n, v in engine.scores.items()}, {'a': 3, 'b': 3})
        self.assertEqual(set(totals), {'a', 'b'})
        pudding_diff = {n: totals[n] - sum(engine.scores[n]) for n in totals}
        self.assertTrue(all(v in (0, 6) for v in pudding_diff.values()))

    def test_pudding_not_double_counted(self):
        engine = self.make_engine()
        engine.start_game()
        engine.players[0].played_cards = [PuddingCard()]
        engine.end_current_round()
        self.assertEqual(engine.players[0].pudding_count, 1)
        engine.end_current_round()  # new round started with an empty table
        self.assertEqual(engine.players[0].pudding_count, 1)

    def test_pudding_penalty_applied_with_three_players(self):
        engine = self.make_engine(('a', 'b', 'c'))
        engine.start_game()
        engine.players[0].pudding_count = 3
        engine.players[1].pudding_count = 1
        engine.players[2].pudding_count = 0
        engine.current_round = engine.max_rounds - 1
        for player in engine.players:
            player.played_cards = []
        totals = engine.end_current_round()
        self.assertEqual(totals, {'a': 6, 'b': 0, 'c': -6})

    def test_chopsticks_keeps_hand_sizes_in_sync_and_round_finishes(self):
        engine = self.make_engine()
        engine.start_game()
        a, b = engine.players
        a.played_cards = [ChopsticksCard()]
        engine.select_and_play_two('a', 0, 1)
        engine.select_and_play('b', 0)
        self.assertEqual(len(a.current_hand), len(b.current_hand))
        self.assertEqual(len(a.current_hand), 9)  # played two, took the chopsticks back
        # finish the round: chopsticks travels around as a normal card
        while engine.current_round == 0:
            for player in engine.players:
                engine.select_and_play(player.name, 0)
        self.assertEqual(engine.current_round, 1)

    def test_chopsticks_with_two_cards_left(self):
        engine = self.make_engine()
        engine.start_game()
        a, b = engine.players
        a.current_hand = a.current_hand[:2]
        b.current_hand = b.current_hand[:2]
        a.played_cards = [ChopsticksCard()]
        engine.select_and_play_two('a', 0, 1)
        engine.select_and_play('b', 0)
        self.assertEqual((len(a.current_hand), len(b.current_hand)), (1, 1))
        engine.select_and_play('a', 0)
        engine.select_and_play('b', 0)
        self.assertEqual(engine.current_round, 1)

    def test_select_and_play_two_same_index_rejected(self):
        engine = self.make_engine()
        engine.start_game()
        engine.players[0].played_cards = [ChopsticksCard()]
        with self.assertRaises(Exception):
            engine.select_and_play_two('a', 2, 2)
        self.assertEqual(len(engine.players[0].current_hand), 10)

    def test_wasabi_boosts_nigiri_through_engine(self):
        engine = self.make_engine()
        engine.start_game()
        a, b = engine.players
        wasabi, squid = WasabiCard(), SquidNigiriCard()
        a.current_hand[0:2] = [wasabi, squid]
        engine.select_and_play('a', 0)
        engine.select_and_play('b', 0)
        # hands swapped; give a the squid back to play it
        a.current_hand.insert(0, squid)
        engine.select_and_play('a', 0)
        self.assertIs(squid.wasabi, wasabi)
        self.assertEqual(engine.scorer.score_for_independent_hand(a.played_cards), 9)
