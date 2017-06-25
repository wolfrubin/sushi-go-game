
def get_largest_and_second_largest(array):
    unique_vals = set(array)
    largest = max(unique_vals)
    second_largest = 0
    for val in unique_vals:
        if val > second_largest and val < largest:
            second_largest = val
    return largest, second_largest

class Scorer:
    
    def score_for_round(self, players):
        independent_scores = []
        for player in players:
            score = self.score_for_independent_hand(player.played_cards)
            independent_scores.append(score)
        maki_scores = self.calculate_maki_scores(players)
        # Needs to be elementwise addition
        # Work out nice way of doing this later
        scores = independent_scores + maki_scores
        return scores

    def calculate_maki_scores(self, players):
        maki_counts = self.calculate_maki_roll_count(map(lambda x:x.played_cards, players))
        return self.maki_score_for_roll_count(maki_counts)

    def maki_score_for_roll_count(self, roll_count):
        calc_first_place = True
        calc_second_place = True

        scores = []
        first_place_score, second_place_score = get_largest_and_second_largest(roll_count)
        if first_place_score == 0:
            calc_first_place = False
        if second_place_score == 0:
            calc_second_place = False
        
        first_places = []
        second_places = []

        for index, count in enumerate(roll_count):
            scores.append(0)
            if count == first_place_score and calc_first_place is not False:
                first_places.append(index)
            if count == second_place_score and calc_second_place is not False:
                second_places.append(index)

        if calc_first_place is not False:
            for first_place_loc in first_places:
                scores[first_place_loc] = 6/len(first_places)
        
        if calc_second_place is not False:
            for second_place_loc in second_places:
                scores[second_place_loc] = 3/len(second_places)

        return scores        

    def calculate_maki_roll_count(self, player_hands):
        maki_counts = []
        for hand in player_hands:
            maki_cards = self.maki_from_hand(hand)
            maki_counts.append(self.roll_count_from_maki(maki_cards))
        return maki_counts

    def roll_count_from_maki(self, maki_cards):
        return sum(map(lambda x : x.number_of_rolls, maki_cards))

    def maki_from_hand(self, hand):
        maki = []
        map(lambda x: maki.append(x) if (x.card_type == "MakiCard") else 0, hand)
        return maki

    def score_for_independent_hand(self, hand):
        # This works for now but will need abstracting when further cards are introduced
        tempura_count = sum(map(lambda x : 1 if (x.card_type == "TempuraCard") else 0, hand))
        dumpling_count = sum(map(lambda x : 1 if (x.card_type == "DumplingCard") else 0, hand))
        sashimi_count = sum(map(lambda x : 1 if (x.card_type == "SashimiCard") else 0, hand))
        nigiri_cards = []
        map(lambda x : nigiri_cards.append(x) if ("NigiriCard" in x.card_type) else 0, hand)
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