from game_engine import GameEngine

if __name__ == "__main__":
    print("Starting game")
    game_engine = GameEngine()

    player_one = game_engine.add_player()
    player_two = game_engine.add_player()

    player_one.name = "Christian"
    player_two.name = "Brandon"

    game_engine.start_game()

    while not game_engine.is_game_complete():
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

