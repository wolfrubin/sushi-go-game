# sushi-go-game
An implementation of the card game SushiGo! in python.

### Still to do
#### Game Engine (/sushi_go)
1. Move game logic from server code to game engine code.

#### Server (/server)
1. Persist games across restarts (currently in memory)

#### React UI (/sugoui)
1. Splash page to request users name
2. Build a working UI for joining, browsing and initialising a game

### SuGoUi module isn't ready for use yet. Currently a work in progress
Next.js 16 / React 19 / Bootstrap 5 (Bootswatch Darkly). From `sugoui/`:
- `npm install`
- `npm run dev` starts a dev server
- `npm run build` exports static files to `sugoui/out` (no Node server needed to host them).
  Set `SUGO_BASE_PATH=/sushi` to build for serving from a sub path.

### How to run
1. From the main directory run `python -m server.game_server`. This starts the game server on port 4136
2. Use the sushi_go_client to send messages to the game server
3. To play a game you need to first create a lobby (CREATE_GAME)
4. Then have other people join the lobby (JOIN_GAME)
5. Once there are 2 or more players you can start a game (START_GAME)
6. Each player can idependently play their cards (PLAY_CARD). The body is a card index e.g. `3`, or two comma separated indexes e.g. `3,5` to play two cards using a chopsticks card already on the table

### Playing from a browser (WebSocket gateway)
`python -m server.gateway` serves the game to browsers over a WebSocket (JSON messages, port 4137) and
also starts the TCP server so both share the same games. It needs `pip install websockets`.
The message format is documented at the top of `server/gateway.py`. Joining a game returns a secret token
that must be sent with every later action for that player.

### Deploying (no Docker)
See `deploy/`: `sushi-go.service` is a hardened systemd unit for the game server and `Caddyfile.snippet`
proxies `wolfrub.in/sushi/ws` to it and serves the static UI from `wolfrub.in/sushi/`.

### Run tests
`python3 -m unittest discover -s tests -t .` (run from the repo root)