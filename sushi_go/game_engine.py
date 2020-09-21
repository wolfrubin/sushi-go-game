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

    def __init__(self, game_name):
        self.deck = Deck()
        self.scorer = Scorer()
        self.scores = {}
        self.game_name = game_name

    def add_player_named(self, player_name):
        if self.players == None:
            self.players = []
        self.players.append(Player(player_name))

    def remove_player(self, player):
        index = self.players.index(player)
        del self.players[index]

    @property
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
        return self.scores
        
    def set_hand_exchange_order(self, hand_exchange_order = None):
        if hand_exchange_order is None:
            self.hand_exchange_order = self.players
        else:
            self.hand_exchange_order = hand_exchange_order
        
    def draw_cards_for_players(self, players):
        for player in players:
            cards = self.deck.draw_random_cards(self.cards_per_player)
            player.current_hand = cards

    def select_and_play(self, player_name, index):
        player = [player for player in self.players if player.name == player_name][0]
        card = player.current_hand[index]
        player.play_card(card)
        return self.progress_game()

    def progress_game(self):
        self.try_exchange_hands()
        if self.is_round_complete() is True:
            return self.end_current_round()
    
    def are_players_ready_next_card(self):
        for player in self.players:
            if player.can_play == True:
                return False
        return True

    def try_exchange_hands(self):
        """
        Use this method when actually playing the game. This prevents
        hands being exchanged prematurely and resets the ready flag.
        """
        if not self.are_players_ready_next_card():
            return False
        self.exchange_hands()
        self.set_players_unready()
        return True

    def exchange_hands(self):
        """
        Here we sequentially swap hands between player pairs.
        [1,2,3,4] => [2,3,4,1]

        index of hand = index of hand + 1 MOD len(players)
        """
        for index, player in enumerate(self.hand_exchange_order[:-1]):
            next_index = index + 1
            self.swap_hands(player, self.hand_exchange_order[next_index])

    def set_players_unready(self):
        for player in self.players:
            player.can_play = True

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
        if self.is_game_complete():
            return self.run_game_complete()
        else:
            return self.start_round()

    def record_scores(self):
        scores = self.scorer.score_for_round(self.players)
        for idx, score in enumerate(scores):
            try:
               self.scores[self.players[idx].name].append(score) 
            except Exception as e:
                self.scores[self.players[idx].name] = [score]

    def is_game_complete(self):
        if self.current_round == self.max_rounds:
            return True
        return False

    def run_game_complete(self):
        end_game_total_scores = {}
        for player in self.players:
            end_game_total_scores[player.name] = sum(self.scores[player])
        return end_game_total_scores

    def __repr__(self):
        return f'Name: {self.game_name} \n Players: {self.players} \n Current Round: {self.current_round}'
