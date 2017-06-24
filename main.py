from cards import TempuraCard, DumplingCard, SashimiCard
from scorer import Scorer
from deck import Deck
from player import Player

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

    def add_player(self):
        if self.players == None:
            self.players = []
        new_player = Player()
        self.players.append(new_player)
        new_player.name = "Player " + str(len(self.players))
        return new_player

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

        for player in self.players:
            self.scores[player] = []

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
        """
        for index, player in enumerate(self.hand_exchange_order[:-1]):
            next_index = index + 1
            if next_index + 1 > len(self.hand_exchange_order):
                next_index = 0
            self.swap_hands(player, self.hand_exchange_order[next_index])

    def set_players_unready(self):
        for player in self.players:
            player.is_ready = False

    def swap_hands(self, player_one, player_two):
        temp_hand_1 = player_one.current_hand
        temp_hand_2 = player_two.current_hand
        player_one.current_hand = temp_hand_2
        player_two.current_hand = temp_hand_1

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
        for player in self.players:
            self.scores[player].append(self.scorer.score_for_hand(player.played_cards))

    def game_complete(self):
        if self.current_round == self.max_rounds:
            return True
        return False

    # def __repr__(self):
    #     return {}

if __name__ == "__main__":
    print("Starting game")
    game_engine = GameEngine()

    player_one = game_engine.add_player()
    player_two = game_engine.add_player()

    player_one.name = "Christian"
    player_two.name = "Brandon"

    game_engine.start_game()

    while not game_engine.game_complete():
        for player in game_engine.players:
            print(str(player.name) + " it's your turn.")
            print("Your cards are " + str(player.current_hand))
            card_index = int(raw_input("Please input an index to play a card: "))
            game_engine.play_card(player, player.current_hand[card_index])
            game_engine.currently_played()
        
        game_engine.try_exchange_hands()
        if game_engine.is_round_complete() is True:
            game_engine.end_current_round()
            print("At the end of this round the scores are as follows.")
            print(game_engine.scores)
            game_engine.start_round()

