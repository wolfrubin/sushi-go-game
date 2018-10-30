from sushi_go.scorer import Scorer

class Player:
    is_ready = False
    name = None
    
    def __init__(self, name):
        self.played_cards = []
        self.current_hand = []
        self.name = name

    def play_card(self, card):
        self.played_cards.append(card)
        del self.current_hand[self.current_hand.index(card)]
        self.is_ready = True

    def add_wasabi(self, nigiri_card, wasabi_card):
        """
        This method is in place for wasabi and nigiri cards.
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

    def __repr__(self):
        return self.name