from sushi_go.scorer import Scorer
from sushi_go.deck import Deck
from sushi_go.player import Player

class GameEngine:
    max_rounds = 3
    current_round = 0
    cards_per_player = None
    players = None
    hand_exchange_order = None
    in_progress = False

    def __init__(self):
        self.deck = Deck()
        self.scorer = Scorer()
        self.scores = {}

    def add_player(self, player):
        if self.players == None:
            self.players = []
        self.players.append(player)

    def remove_player(self, player):
        index = self.players.index(player)
        del self.players[index]

    def number_of_players(self):
        return len(self.players)

    def calc_card_per_player(self, number_of_players):
        self.cards_per_player = 12 - number_of_players

    def start_game(self):
        if self.in_progress:
            raise Exception("Game is in progress and cannot be started.")
        
        if not len(self.players) in range(2,6):
            raise Exception("Incorrect number of players. There can be 2, 3, 4, or 5 players.")

        if self.hand_exchange_order is None:
            self.hand_exchange_order = self.players

        self.calc_card_per_player(len(self.players))

        self.in_progress = True

        self.start_round()

    def start_round(self):
        for player in self.players:
            player.played_cards = []
        self.draw_cards_for_players(self.players)
        
    def set_hand_exchange_order(self, hand_exchange_order = None):
        if hand_exchange_order is None:
            self.hand_exchange_order = self.players
        else:
            self.hand_exchange_order = hand_exchange_order
        
    def draw_cards_for_players(self, players):
        for player in players:
            cards = self.deck.draw_random_cards(self.cards_per_player)
            player.current_hand = cards

    def play_card(self, player, card):
        player.play_card(card)
    
    def are_players_ready_next_card(self):
        for player in self.players:
            if player.is_ready == False:
                return False
        return True

    def try_exchange_hands(self):
        """
        Use this method when actually playing the game. This prevents
        hands being exchanged prematurely and resets the ready flag.
        """
        if self.are_players_ready_next_card() is False:
            return None
        self.exchange_hands()
        self.set_players_unready()

    def exchange_hands(self):
        """
        Here we sequentially swap hands between player pairs.
        [1,2,3,4] => [2,3,4,1]
        Feels inefficient. Should be able to improve.

        index of card = index of card + 1 MOD len(players)
        """
        for index, player in enumerate(self.hand_exchange_order[:-1]):
            next_index = index + 1
            self.swap_hands(player, self.hand_exchange_order[next_index])

    def set_players_unready(self):
        for player in self.players:
            player.is_ready = False

    def swap_hands(self, player_one, player_two):
        player_one.current_hand, player_two.current_hand = player_two.current_hand, player_one.current_hand

    def currently_played(self):
        for player in self.players:
            print(player.name + " has played " + str(player.played_cards))

    def is_round_complete(self):
        for player in self.players:
            if len(player.current_hand) != 0:
                return False
        return True

    def end_current_round(self):
        self.current_round += 1
        self.record_scores()

    def record_scores(self):
        scores = self.scorer.score_for_round(self.players)
        for idx, score in enumerate(scores):
            try:
               self.scores[self.players[idx]].append(score) 
            except Exception as e:
                self.scores[self.players[idx]] = [score]

    def is_game_complete(self):
        if self.current_round == self.max_rounds:
            return True
        return False