import random

class Deck:
    def __init__(self):
        self.cards = []

        for i in range(0,14):
            tc = TempuraCard()
            dc = DumplingCard()
            sc = SashimiCard()
            self.cards.append(tc)
            self.cards.append(dc)
            self.cards.append(sc)

    def draw_random_cards(self, number_of_cards):
        random.shuffle(self.cards)
        return_cards = self.cards[:number_of_cards]
        self.cards = self.cards[number_of_cards:]
        return return_cards

class Card:
    def __repr__(self):
        return self.__class__.__name__

    def __new__(cls, *args, **kwargs):
        if cls is Card:
            raise TypeError("Base card objects cannot be created.")
        return object.__new__(cls, *args, **kwargs)

class TempuraCard(Card):
	pass

class SashimiCard(Card):
    pass

class DumplingCard(Card):
    pass