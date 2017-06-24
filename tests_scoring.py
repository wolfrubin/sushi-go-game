import unittest
from scorer import Scorer
from deck import TempuraCard, DumplingCard, SashimiCard, EggNigiriCard, SalmonNigiriCard, SquidNigiriCard, WasabiCard

"""
Here we test the scoring class. We test all the possible individual
card scoring methods and the hand scoring mechanism.
"""

class TestScoring(unittest.TestCase):

    def setUp(self):
        self.scorer = Scorer()

    def test_score_for_round_integration_one(self):
        cards = [TempuraCard(), TempuraCard(), TempuraCard(),
        DumplingCard(), DumplingCard(), SashimiCard(), SashimiCard()]

        self.assertEqual(self.scorer.score_for_hand(cards), 8)

    def test_score_for_round_integration_two(self):
        sc = SquidNigiriCard()
        wc = WasabiCard()
        sc.wasabi = wc
        cards = [EggNigiriCard(), SquidNigiriCard(), SalmonNigiriCard(), sc]

        self.assertEqual(self.scorer.score_for_hand(cards), 15)

    def test_dumpling_scoring(self):
        self.assertEqual(self.scorer.score_for_dumplings(1),1)
        self.assertEqual(self.scorer.score_for_dumplings(2),3)
        self.assertEqual(self.scorer.score_for_dumplings(3),6)
        self.assertEqual(self.scorer.score_for_dumplings(4),10)
        self.assertEqual(self.scorer.score_for_dumplings(5),15)
        self.assertEqual(self.scorer.score_for_dumplings(6),15)
        self.assertEqual(self.scorer.score_for_dumplings(100),15)

    def test_tempura_scoring(self):
        self.assertEqual(self.scorer.score_for_tempura(1),0)
        self.assertEqual(self.scorer.score_for_tempura(2),5)
        self.assertEqual(self.scorer.score_for_tempura(3),5)
        self.assertEqual(self.scorer.score_for_tempura(4),10)
        self.assertEqual(self.scorer.score_for_tempura(100),250)

    def test_sashimi_scoring(self):
        self.assertEqual(self.scorer.score_for_sashimi(1),0)
        self.assertEqual(self.scorer.score_for_sashimi(2),0)
        self.assertEqual(self.scorer.score_for_sashimi(3),10)
        self.assertEqual(self.scorer.score_for_sashimi(4),10)
        self.assertEqual(self.scorer.score_for_sashimi(20),60)

    def test_scores_egg_nigiri(self):
        en1 = EggNigiriCard()
        en2 = EggNigiriCard()
        self.assertEqual(self.scorer.score_for_nigiri([en1, en2]), 2)
        wc = WasabiCard()
        en1.wasabi = wc
        self.assertEqual(self.scorer.score_for_nigiri([en1,en2]), 4)


if __name__ == "__main__":
    unittest.main()