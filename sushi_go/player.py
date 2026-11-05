from sushi_go.deck import ChopsticksCard, NigiriCard, WasabiCard

class PlayerCannotPlayException(Exception):
    pass

class Player:
    can_play = True
    name = None
    
    def __init__(self, name):
        self.played_cards = []
        self.current_hand = []
        self.pudding_count = 0
        self.name = name

    def play_card(self, card):
        if not self.can_play:
            raise PlayerCannotPlayException()
        self._play_from_hand(card)
        self.can_play = False

    def _play_from_hand(self, card):
        del self.current_hand[self.current_hand.index(card)]
        if isinstance(card, NigiriCard):
            self._attach_unused_wasabi(card)
        self.played_cards.append(card)

    def _attach_unused_wasabi(self, nigiri_card):
        """A wasabi on the table triples the next nigiri played. Attached
        wasabi are removed from played_cards (as in add_wasabi), so any
        wasabi still in played_cards is unused."""
        for played in self.played_cards:
            if isinstance(played, WasabiCard):
                nigiri_card.wasabi = played
                self.played_cards.remove(played)
                return

    @property
    def has_chopsticks(self):
        return any(isinstance(c, ChopsticksCard) for c in self.played_cards)

    def play_two_cards(self, first_card, second_card):
        """Use a chopsticks card on the table to play two cards in one turn.
        The chopsticks go back into the hand to be passed on."""
        if not self.can_play:
            raise PlayerCannotPlayException()
        if first_card is second_card:
            raise Exception("Cannot play the same card twice.")
        if not self.has_chopsticks:
            raise Exception("Cannot play two cards without chopsticks.")
        if first_card not in self.current_hand or second_card not in self.current_hand:
            raise ValueError("Both cards must be in the player's hand.")
        chopsticks = next(c for c in self.played_cards if isinstance(c, ChopsticksCard))
        self._play_from_hand(first_card)
        self._play_from_hand(second_card)
        self.played_cards.remove(chopsticks)
        self.current_hand.append(chopsticks)
        self.can_play = False

    def add_wasabi(self, nigiri_card, wasabi_card):
        """This method is in place for wasabi and nigiri cards.
        A nigiri type card can have a wasabi card placed on it, 
        this doubles the score of the nigiri. (Scorer).

        Could consider moving the method to the card itself.
        """
        if not nigiri_card in self.played_cards or not wasabi_card in self.played_cards:
            raise Exception("Card not in played hand.")
        
        if not "Nigiri" in nigiri_card.card_type:
            raise Exception("Cannot play a wasabi card on a card of type " + nigiri_card.card_type + ".")
        if not "Wasabi" in wasabi_card.card_type:
            raise Exception("Cannot play a non wasabi card using this method.")

        nigiri_card.wasabi = wasabi_card
        del self.played_cards[self.played_cards.index(wasabi_card)]
        self.can_play = False

    def __repr__(self):
        return self.name