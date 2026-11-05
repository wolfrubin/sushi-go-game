# sushi-go-game
An implementation of the card game SushiGo! in python.

### Still to do
#### Game Engine (/sushi_go)
1. Move game logic from server code to game engine code.

#### Server (/server)
1. Fix the websocket implementation to work with the game engine

#### React UI (/sugoui)
1. Mobile layout polish and a visual design pass

### SuGoUi (browser UI)
Next.js 16 / React 19 / Bootstrap 5 (Bootswatch Darkly). From `sugoui/`:
- `npm install`
- `npm run dev` starts a dev server
- `npm run build` exports static files to `sugoui/out` (no Node server needed to host them).
  Set `SUGO_BASE_PATH=/sushi` to build for serving from a sub path.
- `npm test` runs the UI tests (client, storage helpers and component rendering).

During `npm run dev` the UI connects to the game server on `ws://localhost:4137`
(`python -m server.gateway`). In production it connects to `wss://<same host><base path>/ws`.
Set `NEXT_PUBLIC_SUGO_WS_URL` to override.

### How to run
1. From the main directory run `python -m server.game_server`. This starts the game server on port 4136
2. Use the sushi_go_client to send messages to the game server
3. To play a game you need to first create a lobby (CREATE_GAME)
4. Then have other people join the lobby (JOIN_GAME)
5. Once there are 2 or more players you can start a game (START_GAME)
6. Each player can idependently play their cards (PLAY_CARD). The body is a card index e.g. `3`, or two comma separated indexes e.g. `3,5` to play two cards using a chopsticks card already on the table

### Run tests
`python3 -m unittest discover -s tests -t .` (run from the repo root)