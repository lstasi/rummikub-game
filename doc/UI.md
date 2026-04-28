# UI

This document describes the UI that currently ships from `static/`.

## Technology

- Static HTML pages
- Vanilla JavaScript using `fetch`
- Shared utility layer in `static/js/main.js`
- CSS split across `static/css/main.css` and `static/css/game.css`

There is no SPA framework, build step, or component library.

## Pages

### Home Page

Served from `static/pages/home.html`.

Current features:
- Quick-create controls for 2, 3, or 4 players
- My Games column
- Available Games column
- Delete button on owned or visible game cards
- "How to Play" rules dialog through `alert()`
- Polling refresh every 5 seconds

Current API usage:
- `GET /api/v1/games/my-games`
- `GET /api/v1/games?status=waiting_for_players`
- `POST /api/v1/games`
- `POST /api/v1/games/{game_id}/players`
- `DELETE /api/v1/games/{game_id}`

Notes:
- The markup includes a player-info banner, but the current script does not populate it.
- The home page expects `current_player_name`, but the API does not return that field yet.

### Game Page

Served from `static/pages/game.html`.

Current features:
- Polling refresh every 3 seconds while the game is active
- Local board staging before submitting a turn
- Tile selection from the rack
- Button-driven actions:
  - Push selected rack tiles to the board as temporary single-tile entries
  - Remove selected temporary board entries back to the rack
  - Break selected group/run melds into temporary single-tile entries
  - Group selected board entries into a group or run guess
  - Draw tile
  - End turn
  - Reset local turn state
- Rack sorting by number or color
- Inline winner banner on completed games
- Hidden debug panel toggled with `Ctrl+D`

Current local state model:
- `serverGameState`: last server response
- `localBoardState`: in-progress board edits for the acting player
- `playerRackState`: in-progress rack edits for the acting player
- `initialTurnBoardState` and `initialTurnRackState`: reset baselines

Current API usage:
- `GET /api/v1/games/{game_id}/players/{player_id}`
- `POST /api/v1/games/{game_id}/players/{player_id}/actions/play`
- `POST /api/v1/games/{game_id}/players/{player_id}/actions/draw`

### Win Page

Served from `static/pages/win.html`.

Current features:
- Attempts to load the final game state and render winner plus remaining tile counts
- Buttons to clear local storage and return home

Current limitation:
- The main gameplay flow does not currently redirect to this page automatically.

## Tile Rendering

Tile display is derived from tile IDs client-side.

- Jokers render as `J`
- Numbered tiles render the number only
- Color is inferred from the embedded color code

Example mappings:
- `7ra` -> red tile with `7`
- `12kb` -> black tile with `12`
- `ja` -> joker tile

## Polling And Synchronization

### Home Page

- Refresh interval: 5 seconds
- Both lists are reloaded on each cycle

### Game Page

- Refresh interval: 3 seconds
- If the turn changes to the local player, local staged state is reset from the server
- If it is not the local player's turn, the board is forced to the server state
- Draw and play actions also force an immediate state reload after success

## Internationalization

`static/js/i18n.js` supports:
- English (`en`)
- Portuguese (`pt`)
- Spanish (`es`)

Current coverage is partial.

Translated today:
- Core button labels

Not fully translated today:
- Home page headings and inline card text
- Rules dialog body copy
- Most runtime status and error messages

## Responsive Behavior

Current CSS supports:
- Narrower tile sizes on small screens
- Stacked home-page columns below tablet widths
- Wrapping control groups on smaller screens

There is no dedicated mobile interaction model beyond responsive layout.

## Current UX Limitations

- No drag-and-drop support
- No custom login/auth UI
- No move history or audit trail in the interface
- No browser automation coverage yet
- No push-based updates; polling only

Related defects and follow-up work are tracked in `doc/CODE_REVIEW.md` and `TODO.md`.
