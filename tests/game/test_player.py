import unittest
from sushi_go.player import Player
from sushi_go.deck import SquidNigiriCard, WasabiCard, TempuraCard

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
