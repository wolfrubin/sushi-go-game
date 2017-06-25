import unittest
from scorer import Scorer
from deck import TempuraCard, DumplingCard, SashimiCard, EggNigiriCard, SalmonNigiriCard, SquidNigiriCard, WasabiCard, NigiriCard, MakiCard

"""
Here we test the scoring class. We test all the possible individual
card scoring methods and the hand scoring mechanism.
"""

class TestScoring(unittest.TestCase):

    def setUp(self):
        self.scorer = Scorer()

    def test_score_for_round_independent_one(self):
        cards = [TempuraCard(), TempuraCard(), TempuraCard(),
        DumplingCard(), DumplingCard(), SashimiCard(), SashimiCard()]

        self.assertEqual(self.scorer.score_for_independent_hand(cards), 8)

    def test_score_for_round_independent_two(self):
        sc = SquidNigiriCard()
        wc = WasabiCard()
        sc.wasabi = wc
        cards = [EggNigiriCard(), SquidNigiriCard(), SalmonNigiriCard(), sc]

        self.assertEqual(self.scorer.score_for_independent_hand(cards), 15)

    def test_dumpling_scoring(self):
        """
        Various permutations of dumplings scored.
        """
        self.assertEqual(self.scorer.score_for_dumplings(1),1)
        self.assertEqual(self.scorer.score_for_dumplings(2),3)
        self.assertEqual(self.scorer.score_for_dumplings(3),6)
        self.assertEqual(self.scorer.score_for_dumplings(4),10)
        self.assertEqual(self.scorer.score_for_dumplings(5),15)
        self.assertEqual(self.scorer.score_for_dumplings(6),15)
        self.assertEqual(self.scorer.score_for_dumplings(100),15)

    def test_tempura_scoring(self):
        """
        Various permutations of tempura scored.
        """
        self.assertEqual(self.scorer.score_for_tempura(1),0)
        self.assertEqual(self.scorer.score_for_tempura(2),5)
        self.assertEqual(self.scorer.score_for_tempura(3),5)
        self.assertEqual(self.scorer.score_for_tempura(4),10)
        self.assertEqual(self.scorer.score_for_tempura(100),250)

    def test_sashimi_scoring(self):
        """
        Various permutations of sashimi scored.
        """
        self.assertEqual(self.scorer.score_for_sashimi(1),0)
        self.assertEqual(self.scorer.score_for_sashimi(2),0)
        self.assertEqual(self.scorer.score_for_sashimi(3),10)
        self.assertEqual(self.scorer.score_for_sashimi(4),10)
        self.assertEqual(self.scorer.score_for_sashimi(20),60)

    def test_scores_wasabi_nigiri(self):
        """
        Test of the wasabi scoring implementation.
        """
        en1 = EggNigiriCard()
        en2 = EggNigiriCard()
        self.assertEqual(self.scorer.score_for_nigiri([en1, en2]), 2)
        wc = WasabiCard()
        en1.wasabi = wc
        self.assertEqual(self.scorer.score_for_nigiri([en1,en2]), 4)

    def test_scores_maki(self):
        """
        Testing the scoring of maki cards raises an issue not uncovered
        yet. Maki scores are determined by the state of the other players
        in the current round. 
        Scoring Maki cards happens in three stages. First, we map each
        players played_cards to just their MakiCards. Second we map from
        the cards to the total maki_roll numbers. Third we map from roll
        numbers to scores. Points are split between ties in first and second
        place with regard to the total roll numbers.
        e.g. [5,5,1,2] roll scores => [3,3,0,3]. As first place shares 6
        points between two players and second place gets 3 points.
        """
        pass

    def test_calculate_maki_number(self):
        """
        We pass a sequence of hands to this function and we turn it into 
        the total number of Maki to be scored at a later date. This also
        exercises the roll_count_from_maki function.
        """
        mk_1 = MakiCard(3)
        mk_2 = MakiCard(2)
        hand_1 = [mk_1, mk_2]

        mk_3 = MakiCard(1)
        mk_4 = MakiCard(2)
        hand_2 = [mk_3, mk_4]

        mk_5 = MakiCard(1)
        mk_6 = MakiCard(3)
        mk_7 = MakiCard(3)
        hand_3 = [mk_5, mk_6, mk_7]

        self.assertEqual(self.scorer.calculate_maki_roll_count([hand_1, hand_2, hand_3]), [5,3,7])

    def test_maki_from_hand(self):
        """
        This function is needed in Maki scoring to extract only the maki cards
        from a players hand.
        """
        mk_1 = MakiCard(1)
        mk_2 = MakiCard(1)
        tc = TempuraCard()
        wc = WasabiCard()

        hand = [mk_1, mk_2, tc, wc]

        self.assertEqual(self.scorer.maki_from_hand(hand), [mk_1,mk_2])

    def test_score_from_maki_numbers(self):
        """
        We test that the correct scores are assigned in the correct order.
        Given a list of Maki numbers.
        e.g. [5,5,1,2] maki_roll_count => [3,3,0,3] player score addition.
        """
        self.assertEqual(self.scorer.maki_score_for_roll_count([5,0,0,0]), [6,0,0,0])
        self.assertEqual(self.scorer.maki_score_for_roll_count([5,5,1,2]), [3,3,0,3])
        self.assertEqual(self.scorer.maki_score_for_roll_count([5,3,0,0]), [6,3,0,0])
        self.assertEqual(self.scorer.maki_score_for_roll_count([5,1,1,1]), [6,1,1,1])
        self.assertEqual(self.scorer.maki_score_for_roll_count([5,5,5,3]), [2,2,2,3])
        self.assertEqual(self.scorer.maki_score_for_roll_count([0,0,0,0]), [0,0,0,0])

    def test_score_for_round(self):
        """
        To test the score for round functionality we must have players
        with Maki type cards.
        """
        pass


if __name__ == "__main__":
    unittest.main()