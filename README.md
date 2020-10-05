# sushi-go-game
An implementation of the card game SushiGo! in python.

### Still to do
#### Game Engine (/sushi_go)
1. Move game logic from server code to game engine code.
2. Fix the way that the initial deck is generated.
3. Add the ability to add wasabi to nigiri cards in server.
4. Add the chopstick type card.

#### Server (/server)
1. Fix the websocket implementation to work with the game engine

#### React UI (/sugoui)
1. Splash page to request users name
2. Build a working UI for joining, browsing and initialising a game

### SuGoUi module isn't ready for use yet. Currently a work in progress
`npm run dev` will start a dev server

### How to run
1. From the main directory run `python -m server.game_server`. This starts the game server on port 4136
2. Use the sushi_go_client to send messages to the game server
3. To play a game you need to first create a lobby (CREATE_GAME)
4. Then have other people join the lobby (JOIN_GAME)
5. Once there are 2 or more players you can start a game (START_GAME)
6. Each player can idependently play their cards (PLAY_CARD)

### Run tests
`python3 -m unittest discover tests`