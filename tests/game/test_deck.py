import unittest
from collections import Counter
from sushi_go.deck import (
    Deck, Card, MakiCard, TempuraCard, ChopsticksCard, PuddingCard, WasabiCard,
    NigiriCard, SquidNigiriCard, OneRollMakiCard, TwoRollMakiCard, ThreeRollMakiCard,
    CARD_TYPE_DISTRIBUTION,
)


class TestDeck(unittest.TestCase):

    def setUp(self):
        self.deck = Deck()

    def test_deck_matches_distribution(self):
        counts = Counter(type(card) for card in self.deck.cards)
        self.assertEqual(dict(counts), CARD_TYPE_DISTRIBUTION)
        self.assertEqual(len(self.deck), 108)

    def test_deck_contains_special_cards(self):
        self.assertEqual(sum(isinstance(c, PuddingCard) for c in self.deck.cards), 10)
        self.assertEqual(sum(isinstance(c, ChopsticksCard) for c in self.deck.cards), 4)
        self.assertEqual(sum(isinstance(c, WasabiCard) for c in self.deck.cards), 6)

    def test_cards_are_distinct_objects(self):
        # Wasabi is stored per card, so cards must never be shared
        self.assertEqual(len({id(c) for c in self.deck.cards}), 108)

    def test_draw_removes_cards_from_deck(self):
        drawn = self.deck.draw_random_cards(10)
        self.assertEqual(len(drawn), 10)
        self.assertEqual(len(self.deck), 98)
        for card in drawn:
            self.assertNotIn(card, self.deck.cards)

    def test_draw_zero_cards(self):
        self.assertEqual(self.deck.draw_random_cards(0), [])
        self.assertEqual(len(self.deck), 108)

    def test_draw_entire_deck_then_fail(self):
        self.assertEqual(len(self.deck.draw_random_cards(108)), 108)
        self.assertEqual(len(self.deck), 0)
        with self.assertRaises(Exception):
            self.deck.draw_random_cards(1)

    def test_separate_decks_are_independent(self):
        other = Deck()
        self.deck.draw_random_cards(20)
        self.assertEqual(len(other), 108)


class TestCards(unittest.TestCase):

    def test_base_card_cannot_be_created(self):
        with self.assertRaises(TypeError):
            Card()

    def test_base_maki_card_cannot_be_created(self):
        with self.assertRaises(TypeError):
            MakiCard()

    def test_card_type_and_repr(self):
        card = TempuraCard()
        self.assertEqual(card.card_type, 'TempuraCard')
        self.assertEqual(repr(card), 'TempuraCard')

    def test_multiplying_a_card_gives_new_cards(self):
        cards = TempuraCard() * 3
        self.assertEqual(len(cards), 3)
        self.assertTrue(all(isinstance(c, TempuraCard) for c in cards))
        self.assertEqual(len({id(c) for c in cards}), 3)

    def test_nigiri_has_no_wasabi_by_default_and_not_shared(self):
        a, b = SquidNigiriCard(), SquidNigiriCard()
        self.assertIsNone(a.wasabi)
        a.wasabi = WasabiCard()
        self.assertIsNone(b.wasabi)
        self.assertIsInstance(a, NigiriCard)

    def test_maki_roll_numbers(self):
        self.assertEqual(OneRollMakiCard.number_of_rolls, 1)
        self.assertEqual(TwoRollMakiCard.number_of_rolls, 2)
        self.assertEqual(ThreeRollMakiCard.number_of_rolls, 3)
