from cards import TempuraCard, DumplingCard, SashimiCard
from scorer import Scorer
from player_number_getter import PlayerNumberGetter
from deck import Deck
from player import Player

class GameEngine:
    max_rounds = 1
    current_round = 0
    cards_per_player = None
    players = None
    hand_exchange_order = None
    in_progress = False

    def __init__(self):
        self.deck = Deck()

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

        self.calc_card_per_player(len(self.players))

        for player in self.players:
            cards = self.deck.draw_random_cards(self.cards_per_player)
            player.current_hand = cards

        if self.hand_exchange_order is None:
            self.hand_exchange_order = self.players
        
        self.in_progress = True
        
    def play_card(self, player, card):
        player.play_card(card)
    
    def are_players_ready_next_card(self):
        all_ready = True
        for player in self.players:
            if player.is_ready == False:
                all_ready = False
                break
        return all_ready

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

    def round_complete(self):
        round_complete = True
        for player in self.players:
            if len(player.current_hand) != 0:
                round_complete = False
                break
        return round_complete

    def game_complete(self):
        if self.current_round == self.max_rounds:
            

    def __repr__(self):
        return {}

if __name__ == "__main__":
    print("Starting game")
    game_engine = GameEngine()

    player_one = game_engine.add_player()
    player_two = game_engine.add_player()
    player_three = game_engine.add_player()
    player_four = game_engine.add_player()

    player_one.name = "Christian"
    player_two.name = "Brandon"
    player_three.name = "Cara"
    player_four.name = "Karin"

    game_engine.start_game()

    while True:
        for player in game_engine.players:
            print(str(player.name) + " it's your turn.")
            print("Your cards are " + str(player.current_hand))
            card_index = int(raw_input("Please input an index to play a card: "))
            game_engine.play_card(player, player.current_hand[card_index])
            game_engine.currently_played()
            game_engine.try_exchange_hands()
            if game_engine.round_complete() is True:
                for player in game_engine.players:
                    player.print_score()
                print("Round complete")
                break