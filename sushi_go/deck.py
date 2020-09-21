import random


class Deck(object):
    def __init__(self):
        """
        This can be improved by creating initialising with a ruleset.
        This ruleset will be modifiable so we can have different games.
        """
        self.cards = []

        for card_type, number in CARD_TYPE_DISTRIBUTION.items():
            self.cards += (card_type() * number)

    def draw_random_cards(self, number_of_cards):
        if number_of_cards > len(self.cards):
            raise Exception("Tried to withdraw too many cards. There are " + str(len(self.cards)) + " cards left in this deck.")
        random.shuffle(self.cards)
        return_cards = self.cards[:number_of_cards]
        self.cards = self.cards[number_of_cards:]
        return return_cards

    def __len__(self):
        return len(self.cards)


class Card(object):
    def __repr__(self):
        return self.__class__.__name__

    def __new__(cls, *args, **kwargs):
        if cls is Card:
            raise TypeError("Base card objects cannot be created.")
        return object.__new__(cls)

    def __mul__(self, other):
        # Multiplying a card by an integer returns a list of cards
        try:
            int(other)
        except ValueError: 
            pass
        else:
            return [self.__class__() for _ in range(other)] 

    def __init__(self, *args, **kwargs):
        self.card_type = self.__class__.__name__

class TempuraCard(Card):
	pass

class SashimiCard(Card):
    pass

class DumplingCard(Card):
    pass

class NigiriCard(Card):
    wasabi = None

class SquidNigiriCard(NigiriCard):
    pass

class SalmonNigiriCard(NigiriCard):
    pass

class EggNigiriCard(NigiriCard):
    pass

class WasabiCard(Card):
    pass


class MakiCard(Card):
    
    def __new__(cls, *args, **kwargs):
        if cls is MakiCard:
            raise TypeError("MakiCard objects cannot be created. Use a subtype instead.")
        return object.__new__(cls)


class OneRollMakiCard(MakiCard):
    number_of_rolls = 1

class TwoRollMakiCard(MakiCard):
    number_of_rolls = 2

class ThreeRollMakiCard(MakiCard):
    number_of_rolls = 3

CARD_TYPE_DISTRIBUTION = {
    TempuraCard: 14,
    SashimiCard: 14,
    DumplingCard: 14,
    SquidNigiriCard: 5,
    SalmonNigiriCard: 5,
    EggNigiriCard: 5,
    WasabiCard: 5,
    OneRollMakiCard: 4,
    TwoRollMakiCard: 4,
    ThreeRollMakiCard: 4,
}
