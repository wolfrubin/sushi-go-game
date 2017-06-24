
class Scorer:
    
    def score_for_hand(self, hand):
        # This works for now but will need abstracting when further cards are introduced
        tempura_count = sum(map(lambda x : 1 if (x.card_type == "TempuraCard") else 0, hand))
        dumpling_count = sum(map(lambda x : 1 if (x.card_type == "DumplingCard") else 0, hand))
        sashimi_count = sum(map(lambda x : 1 if (x.card_type == "SashimiCard") else 0, hand))
        nigiri_cards = set()
        map(lambda x : nigiri_cards.add(x) if ("NigiriCard" in x.card_type) else 0, hand)
        score = self.score_for_dumplings(dumpling_count) + self.score_for_tempura(tempura_count) + self.score_for_sashimi(sashimi_count) + self.score_for_nigiri(nigiri_cards)
        return score

    def score_for_dumplings(self, number_of_dumplings):
        score = 0
        for i in range(1,number_of_dumplings+1):
            score += i
            if score >= 15:
                break
        if score > 15:
            score = 15
        return score

    def score_for_tempura(self, number_of_tempura):
        return ((number_of_tempura/2) * 5)
        
    def score_for_sashimi(self, number_of_sashimi):
        return ((number_of_sashimi/3) * 10)

    def score_for_nigiri(self, nigiri_cards):
        """
        Here we need to score the nigiri cards. We need the card objects
        as they contain the wasabi that doubles the score.
        """
        score = 0
        for card in nigiri_cards:
            card_score = 0
            if card.card_type == "EggNigiriCard":
                card_score = 1
            if card.card_type == "SalmonNigiriCard":
                card_score = 2
            if card.card_type == "SquidNigiriCard":
                card_score = 3

            if card.wasabi is not None:
                card_score = card_score * 3

            score += card_score

        return score