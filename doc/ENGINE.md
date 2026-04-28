# Game Engine

This document describes the engine that is currently implemented in `src/rummikub/engine/`.

## Overview

The engine is split across three modules:

- `game_engine.py`: public façade
- `game_actions.py`: state transitions
- `game_rules.py`: validation helpers and win checks

The engine is stateless. Each method accepts a `GameState` and returns a new `GameState`.

## Public API

### Lifecycle

```python
GameEngine.create_game(num_players: int) -> GameState
GameEngine.join_game(game_state: GameState, player_name: str) -> GameState
GameEngine.start_game(game_state: GameState) -> GameState
GameEngine.get_game_status(game_state: GameState) -> GameStatus
```

Behavior:
- `create_game()` delegates to `GameState.create_initialized_game()`.
- `join_game()` assigns the supplied name to the first unjoined player slot.
- When all slots are joined, `join_game()` auto-starts the game.
- `start_game()` still exists, but the API flow relies on auto-start rather than manual start.

### Turn And Actions

```python
GameEngine.get_current_player(game_state: GameState) -> str
GameEngine.can_player_act(game_state: GameState, player_id: str) -> bool
GameEngine.advance_turn(game_state: GameState) -> GameState
GameEngine.execute_play_action(game_state: GameState, player_id: str, action: PlayTilesAction) -> GameState
GameEngine.execute_draw_action(game_state: GameState, player_id: str) -> GameState
```

### Validation Helpers

```python
GameEngine.validate_initial_meld(melds: list[Meld]) -> bool
GameEngine.check_win_condition(game_state: GameState, player_id: str) -> bool
```

## Game Setup Model

The engine uses pre-dealt player slots.

1. `create_game(num_players)` builds the full pool.
2. Fourteen tiles are dealt to every seat immediately.
3. Players are created with `joined=False` and `name=None`.
4. Joining a game attaches a name to an existing seat.
5. When the final seat is joined, the game status becomes `in_progress`.

This means pool size is already reduced before anyone joins.

## Play Action Contract

`PlayTilesAction.melds` represents the complete board end-state after the player's move.

Current validation pipeline in `GameActions.execute_play_action()`:

1. Validate turn ownership.
2. Load the acting player.
3. Compute `newly_played_tiles` as submitted-board tiles minus current-board tiles.
4. Reject empty plays with no newly played tiles.
5. Validate the player owns the newly played tiles.
6. Validate every submitted meld.
7. Validate the initial meld threshold if the player has not met it yet.
8. Remove newly played tiles from the player's rack.
9. Replace the board with the submitted meld list.
10. Check win condition and otherwise advance the turn.

## Draw Action Contract

Current draw flow:

1. Validate turn ownership.
2. Validate the pool is not empty.
3. Draw one random tile from the pool.
4. Add it to the acting player's rack.
5. Advance the turn.

## Rule Enforcement

Implemented rule checks include:

- Player turn validation
- Meld-size checks
- Meld-content validation through `Meld.validate()`
- Initial meld total of at least 30 points
- Draw-from-empty-pool rejection
- Empty-play rejection
- Win detection based on an empty rack and `initial_meld_met=True`

## Exceptions Used By The Engine

- `GameStateError`
- `GameNotStartedError`
- `GameFinishedError`
- `GameFullError`
- `NotPlayersTurnError`
- `PlayerNotInGameError`
- `InvalidMoveError`
- `InitialMeldNotMetError`
- `TileNotOwnedError`
- `PoolEmptyError`
- `InvalidBoardStateError`

## Current Limitations

- The engine does not yet guarantee that a submitted board preserves every previously-board tile.
- Win paths set `status=completed`, but do not consistently populate `winner_player_id`.
- `start_game()` checks seat count rather than joined-player count, so it behaves more like an escape hatch than the public lifecycle path.

See `doc/CODE_REVIEW.md` for priority and remediation notes.
