from sushi_go.scorer import Scorer
from sushi_go.deck import Deck, PuddingCard
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
        self.players = []
        self.finished = False
        self.final_scores = None
        self.last_round = None

    def is_player_in(self, player_name):
        return player_name in map(lambda x: x.name, self.players)

    def add_player_named(self, player_name):
        if self.is_player_in(player_name):
            raise Exception("A player with that name has already joined the game")
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

    def _player_named(self, player_name):
        return [player for player in self.players if player.name == player_name][0]

    def _check_playable(self):
        if self.finished:
            raise Exception("The game is finished.")

    def select_and_play(self, player_name, index):
        self._check_playable()
        player = self._player_named(player_name)
        card = player.current_hand[index]
        player.play_card(card)
        return self.progress_game()

    def select_and_play_two(self, player_name, first_index, second_index):
        """Play two cards in one turn using a chopsticks card."""
        self._check_playable()
        player = self._player_named(player_name)
        if first_index == second_index:
            raise Exception("Cannot play the same card twice.")
        first = player.current_hand[first_index]
        second = player.current_hand[second_index]
        player.play_two_cards(first, second)
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
        self.collect_puddings()
        self.last_round = self.summarise_round()
        if self.is_game_complete():
            return self.run_game_complete()
        else:
            return self.start_round()

    def record_scores(self):
        scores = self.scorer.score_for_round(self.players)
        for idx, score in enumerate(scores):
            self.scores.setdefault(self.players[idx].name, []).append(score)

    def collect_puddings(self):
        """Puddings are kept between rounds and only scored at game end."""
        for player in self.players:
            player.pudding_count += sum(
                1 for card in player.played_cards if isinstance(card, PuddingCard))

    def summarise_round(self):
        """What was on each table and what it scored, kept after the tables
        are cleared for the next round so clients can show the result."""
        return {
            "number": self.current_round,
            "players": {
                player.name: {
                    "played": [card.to_dict() for card in player.played_cards],
                    "score": self.scores[player.name][-1],
                }
                for player in self.players
            },
        }

    def status(self):
        if self.finished:
            return "finished"
        return "playing" if self.in_progress else "lobby"

    def state_for(self, player_name):
        """JSON friendly view of the game for one player. Only that player's
        own hand is included, opponents only expose how many cards they hold."""
        me = self._player_named(player_name)
        playing = self.status() == "playing"
        return {
            "game": self.game_name,
            "status": self.status(),
            "round": min(self.current_round + (0 if self.finished else 1), self.max_rounds),
            "max_rounds": self.max_rounds,
            "you": me.name,
            "hand": [card.to_dict() for card in me.current_hand],
            "can_play": playing and me.can_play,
            "can_use_chopsticks": playing and me.can_play and me.has_chopsticks and len(me.current_hand) >= 2,
            "players": [
                {
                    "name": player.name,
                    "played": [card.to_dict() for card in player.played_cards],
                    "hand_size": len(player.current_hand),
                    "has_played": playing and not player.can_play,
                    "pudding": player.pudding_count,
                    "scores": list(self.scores.get(player.name, [])),
                }
                for player in self.players
            ],
            "last_round": self.last_round,
            "final_scores": self.final_scores,
        }

    def is_game_complete(self):
        if self.current_round == self.max_rounds:
            return True
        return False

    def run_game_complete(self):
        pudding_scores = self.scorer.score_for_puddings(
            [player.pudding_count for player in self.players])
        end_game_total_scores = {}
        for player, pudding_score in zip(self.players, pudding_scores):
            end_game_total_scores[player.name] = sum(self.scores[player.name]) + pudding_score
        self.finished = True
        self.final_scores = end_game_total_scores
        return end_game_total_scores

    def __repr__(self):
        return f'Name: {self.game_name} \n Players: {self.players} \n Current Round: {self.current_round}'
