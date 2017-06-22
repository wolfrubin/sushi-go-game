from scorer import Scorer

class Player:
    is_ready = False
    name = None
    
    def __init__(self):
        self.played_cards = []
        self.current_hand = []
        self.scorer = Scorer()

    def score_for_round(self):
        return self.scorer.score_for_hand(self.played_cards)

    def play_card(self, card):
        self.played_cards.append(card)
        del self.current_hand[self.current_hand.index(card)]
        self.is_ready = True

    def print_score(self):
        print(self.score_for_round())