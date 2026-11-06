import unittest
from sushi_go.player import Player, PlayerCannotPlayException
from sushi_go.deck import (SquidNigiriCard, WasabiCard, TempuraCard, EggNigiriCard,
                           ChopsticksCard, SashimiCard, DumplingCard)

class TestPlayer(unittest.TestCase):
    
    def setUp(self):
        self.player = Player('Bar')
        self.wasabi_card = WasabiCard()
        self.squid_nigiri_card = SquidNigiriCard()
        
        self.player.played_cards = [self.squid_nigiri_card, self.wasabi_card]

    def test_add_wasabi_failure_unplayed_card(self):
        tempura_card = TempuraCard()

        with self.assertRaises(Exception) as context:
            self.player.add_wasabi(tempura_card, self.wasabi_card)
            self.assertTrue("Card not in played hand." in context)

    def test_add_wasabi_failure_not_nigiri(self):
        tempura_card = TempuraCard()

        with self.assertRaises(Exception) as context:
            self.player.add_wasabi(tempura_card, self.wasabi_card)
            self.assertTrue("Cannot play a wasabi card" in context)

    def test_add_wasabi_failure_not_wasabi(self):
        tempura_card = TempuraCard()

        with self.assertRaises(Exception) as context:
            self.player.add_wasabi(self.squid_nigiri_card, tempura_card)
            self.assertTrue("Cannot play a non wasabi card" in context)

    def test_add_wasabi_success(self):
        """
        A success in this case is that the squid nigiri has a wasabi
        attached to it and that the count of played cards is reduced.
        """
        self.player.add_wasabi(self.squid_nigiri_card, self.wasabi_card)

        self.assertEqual(len(self.player.played_cards), 1)
        self.assertEqual(self.squid_nigiri_card.wasabi, self.wasabi_card)


class TestPlayerSpecialCards(unittest.TestCase):

    def setUp(self):
        self.player = Player('Foo')

    def test_nigiri_played_after_wasabi_is_tripled(self):
        wasabi, squid = WasabiCard(), SquidNigiriCard()
        self.player.current_hand = [wasabi, squid]
        self.player.play_card(wasabi)
        self.player.can_play = True
        self.player.play_card(squid)

        self.assertIs(squid.wasabi, wasabi)
        self.assertEqual(self.player.played_cards, [squid])

    def test_wasabi_only_applies_to_one_nigiri(self):
        wasabi, egg_one, egg_two = WasabiCard(), EggNigiriCard(), EggNigiriCard()
        self.player.current_hand = [wasabi, egg_one, egg_two]
        for card in (wasabi, egg_one, egg_two):
            self.player.can_play = True
            self.player.play_card(card)

        self.assertIs(egg_one.wasabi, wasabi)
        self.assertIsNone(egg_two.wasabi)

    def test_nigiri_played_before_wasabi_is_not_boosted(self):
        wasabi, egg = WasabiCard(), EggNigiriCard()
        self.player.current_hand = [egg, wasabi]
        self.player.play_card(egg)
        self.player.can_play = True
        self.player.play_card(wasabi)

        self.assertIsNone(egg.wasabi)

    def test_chopsticks_play_two_cards_and_return_to_hand(self):
        chopsticks, tempura, sashimi, dumpling = ChopsticksCard(), TempuraCard(), SashimiCard(), DumplingCard()
        self.player.played_cards = [chopsticks]
        self.player.current_hand = [tempura, sashimi, dumpling]

        self.player.play_two_cards(tempura, sashimi)

        self.assertEqual(self.player.played_cards, [tempura, sashimi])
        self.assertEqual(self.player.current_hand, [dumpling, chopsticks])
        self.assertFalse(self.player.can_play)

    def test_chopsticks_required_for_two_cards(self):
        tempura, sashimi = TempuraCard(), SashimiCard()
        self.player.current_hand = [tempura, sashimi]
        with self.assertRaises(Exception):
            self.player.play_two_cards(tempura, sashimi)
        self.assertEqual(len(self.player.current_hand), 2)

    def test_chopsticks_cannot_play_same_card_twice(self):
        tempura = TempuraCard()
        self.player.played_cards = [ChopsticksCard()]
        self.player.current_hand = [tempura, SashimiCard()]
        with self.assertRaises(Exception):
            self.player.play_two_cards(tempura, tempura)

    def test_chopsticks_wasabi_then_nigiri_in_one_turn(self):
        wasabi, squid = WasabiCard(), SquidNigiriCard()
        self.player.played_cards = [ChopsticksCard()]
        self.player.current_hand = [wasabi, squid]
        self.player.play_two_cards(wasabi, squid)
        self.assertIs(squid.wasabi, wasabi)


class TestPlayerTurnRules(unittest.TestCase):

    def setUp(self):
        self.player = Player('Baz')
        self.tempura, self.sashimi = TempuraCard(), SashimiCard()
        self.player.current_hand = [self.tempura, self.sashimi]

    def test_play_card_moves_card_and_blocks_further_plays(self):
        self.player.play_card(self.tempura)
        self.assertEqual(self.player.played_cards, [self.tempura])
        self.assertEqual(self.player.current_hand, [self.sashimi])
        self.assertFalse(self.player.can_play)
        with self.assertRaises(PlayerCannotPlayException):
            self.player.play_card(self.sashimi)
        self.assertEqual(self.player.current_hand, [self.sashimi])

    def test_play_card_not_in_hand_leaves_state_untouched(self):
        with self.assertRaises(ValueError):
            self.player.play_card(DumplingCard())
        self.assertTrue(self.player.can_play)
        self.assertEqual(self.player.played_cards, [])
        self.assertEqual(len(self.player.current_hand), 2)

    def test_chopsticks_blocked_when_already_played_this_turn(self):
        self.player.played_cards = [ChopsticksCard()]
        self.player.can_play = False
        with self.assertRaises(PlayerCannotPlayException):
            self.player.play_two_cards(self.tempura, self.sashimi)

    def test_chopsticks_invalid_second_card_is_atomic(self):
        """A failed chopsticks play must not leave a half played turn."""
        chopsticks = ChopsticksCard()
        self.player.played_cards = [chopsticks]
        with self.assertRaises(Exception):
            self.player.play_two_cards(self.tempura, DumplingCard())
        self.assertEqual(self.player.played_cards, [chopsticks])
        self.assertEqual(self.player.current_hand, [self.tempura, self.sashimi])
        self.assertTrue(self.player.can_play)

    def test_chopsticks_only_one_set_used_at_a_time(self):
        first, second = ChopsticksCard(), ChopsticksCard()
        self.player.played_cards = [first, second]
        self.player.play_two_cards(self.tempura, self.sashimi)
        self.assertEqual(self.player.played_cards.count(second), 1)
        self.assertEqual(sum(isinstance(c, ChopsticksCard) for c in self.player.current_hand), 1)

    def test_has_chopsticks(self):
        self.assertFalse(self.player.has_chopsticks)
        self.player.played_cards.append(ChopsticksCard())
        self.assertTrue(self.player.has_chopsticks)

    def test_new_player_starts_with_no_puddings(self):
        self.assertEqual(self.player.pudding_count, 0)
