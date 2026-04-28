# Code Review

This document captures the current review findings from a full repository pass.

## Findings

### 1. Critical: Player-scoped endpoints are not bound to the authenticated caller

Affected code:
- `src/rummikub/api/main.py`
- `src/rummikub/api/dependencies.py`

Problem:
- `GET /games/{game_id}/players/{player_id}` does not require auth.
- `POST /games/{game_id}/players/{player_id}/actions/play` does not require auth.
- `POST /games/{game_id}/players/{player_id}/actions/draw` does not require auth.
- `DELETE /games/{game_id}` does not require auth.

Impact:
- Anyone who knows a `player_id` can request that player's curated view.
- Anyone who knows a `player_id` can submit play and draw actions as that player.
- Because player IDs are returned in game responses, this is an impersonation and privacy issue, not just an internal API concern.
- Any caller who knows a game ID can delete the game.

Recommended fix:
- Require Basic Auth on player-scoped routes.
- Resolve the authenticated player name to the expected player record in the game.
- Reject mismatches between auth identity and path `player_id`.
- Decide whether delete should require the creator, a participant, or an admin capability.

Tests to add:
- Unauthorized state fetch
- Unauthorized draw action
- Unauthorized play action
- Delete by non-owner or unauthenticated caller

### 2. Critical: Play actions can silently drop existing board tiles

Affected code:
- `src/rummikub/engine/game_actions.py`
- `src/rummikub/engine/game_rules.py`
- `src/rummikub/models/game.py`

Problem:
- `execute_play_action()` computes `newly_played_tiles` only as submitted-board tiles minus current-board tiles.
- It validates ownership only for those newly played tiles.
- It then replaces the board wholesale with `Board.replace_melds(action.melds)`.
- There is no post-move validation that every tile formerly on the board is still present exactly once.

Impact:
- A client can submit a board that omits an existing board tile while also adding at least one legitimate tile from their rack.
- The move can pass validation and permanently erase board tiles from the game state.
- This is a state-corruption issue that breaks the core tile-partition invariant.

Recommended fix:
- Validate the full tile partition after every play action.
- Explicitly compare previous-board tiles and resulting-board tiles.
- Reject missing or duplicated tiles before persisting.

Tests to add:
- Rearrangement that drops an existing board tile
- Rearrangement that duplicates an existing board tile
- Regression coverage at engine, service, and API layers

### 3. High: Completed games do not reliably set `winner_player_id`

Affected code:
- `src/rummikub/engine/game_actions.py`
- `src/rummikub/engine/game_rules.py`
- `tests/service/game_simulation_tests.py`

Problem:
- Win paths mark the game as `completed` but do not consistently populate `winner_player_id`.
- Existing scenario tests already document this as a TODO and work around it by checking for an empty winning rack instead.

Impact:
- API responses cannot reliably identify the winner.
- Game page and win page fall back to `Unknown Player`.
- Downstream UX and any future scoring or history features are incomplete.

Recommended fix:
- Set `winner_player_id` whenever the engine transitions to `GameStatus.COMPLETED` because of a win.
- Add regression tests in engine, service, API, and UI-facing flows.

### 4. Medium: Home page expects `current_player_name`, but the API does not return it

Affected code:
- `static/js/home.js`
- `src/rummikub/api/models.py`
- `src/rummikub/api/main.py`

Problem:
- The home page checks `game.current_player_name` to render turn information.
- `GameStateResponse` does not define or populate `current_player_name`.

Impact:
- The intended current-turn label on home-page cards never appears.

Recommended fix:
- Either add `current_player_name` to the API response, or derive it client-side from the `players` array and `current_player_index`.

### 5. Medium: Home-page player banner and translation coverage are incomplete

Affected code:
- `static/pages/home.html`
- `static/js/home.js`
- `static/js/i18n.js`

Problem:
- The home page includes a hidden player-info banner, but the script never populates or shows it.
- The redesigned home page and rules dialog still contain hard-coded English copy outside the translation map.

Impact:
- The UI looks partially finished.
- Language support is inconsistent across the shipped experience.

Recommended fix:
- Wire the banner to the authenticated player identity.
- Move the remaining hard-coded strings into `i18n.js`.
- Replace the `alert()` rules dialog with a translatable modal.

## Residual Risks

- Redis locking is simple and good enough for low contention, but not for higher concurrency.
- The dedicated win page exists, but the main gameplay flow ends inline rather than navigating there.
- There are no UI automation tests yet.

## Recommended Order

1. Lock down authorization on player-scoped and destructive routes.
2. Enforce board-tile conservation on play actions.
3. Fix `winner_player_id` and add regressions.
4. Clean up home-page contract mismatches and translation gaps.