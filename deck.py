import random

class Deck:
    def __init__(self):
        """
        This can be improved by creating initialising with a ruleset.
        This ruleset will be modifiable so we can have different games.
        """
        self.cards = []

        for i in range(0,14):
            tc = TempuraCard()
            dc = DumplingCard()
            sc = SashimiCard()
            self.cards.append(tc)
            self.cards.append(dc)
            self.cards.append(sc)

        for i in range(0,6):
            en = EggNigiriCard()
            saln = SalmonNigiriCard()
            sqn = SquidNigiriCard()
            wc = WasabiCard()
            self.cards.append(en)
            self.cards.append(saln)
            self.cards.append(sqn)
            self.cards.append(wc)

    def draw_random_cards(self, number_of_cards):
        if number_of_cards > len(self.cards):
            raise Exception("Tried to withdraw too many cards. There are " + str(len(self.cards)) + " cards left in this deck.")
        random.shuffle(self.cards)
        return_cards = self.cards[:number_of_cards]
        self.cards = self.cards[number_of_cards:]
        return return_cards

    def __len__(self):
        return len(self.cards)


class Card:
    def __repr__(self):
        return self.__class__.__name__

    def __new__(cls, *args, **kwargs):
        if cls is Card:
            raise TypeError("Base card objects cannot be created.")
        return object.__new__(cls, *args, **kwargs)

    def __init__(self):
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