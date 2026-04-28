# Domain Models

This document describes the model layer that is currently implemented in `src/rummikub/models/`.

## Design Summary

The repository uses Python dataclasses for domain state and plain string tile IDs for physical tiles.

Core modules:
- `tiles.py`
- `melds.py`
- `game.py`
- `actions.py`
- `exceptions.py`
- `name_generator.py`

## Tile Representation

There is no runtime `TileInstance` wrapper object in the current implementation. Physical tiles are represented directly by deterministic string IDs.

### Numbered Tiles

Format:

```text
{number}{color_code}{copy}
```

Examples:
- `7ra` -> red 7, copy A
- `12kb` -> black 12, copy B

Color codes:
- `k` -> black
- `r` -> red
- `b` -> blue
- `o` -> orange

Copies:
- `a`
- `b`

### Joker Tiles

Format:

```text
j{copy}
```

Examples:
- `ja`
- `jb`

### Tile Utility API

`TileUtils` provides helpers to:
- detect joker vs numbered tiles
- extract number, color, copy, and value
- create numbered tile IDs and joker IDs
- create the full 106-tile set
- format tile IDs for display

## Validation-Only Tile Kinds

`tiles.py` still defines lightweight validation models:
- `NumberedTile(number, color)`
- `JokerTile()`

These are used for joker assignment and meld value calculation, not as the main persisted tile representation.

## Melds

`Meld` is a dataclass with:
- `kind: MeldKind`
- `tiles: list[str]`
- `id: str` derived automatically

### Meld Kinds

- `group`
- `run`

### Group Rules

- size must be 3 or 4
- all numbered tiles must share the same number
- all numbered tiles must have distinct colors
- jokers fill missing colors for that number

### Run Rules

- size must be at least 3
- all numbered tiles must share the same color
- numbered tiles must be consecutive in sequence order
- jokers fill missing numbers based on their position in the run
- sequences cannot go below 1 or above 13

### Deterministic Meld IDs

- Group IDs are sorted by color order: black, red, blue, orange, then jokers
- Run IDs preserve sequence order
- The ID is the joined tile list with `-`

Examples:
- Group: `7ka-7ra-7ba`
- Run: `5ra-6ra-7ra`

## Game State Objects

### Rack

- stores `tile_ids: list[str]`
- supports initial-rack validation

### Pool

- stores `tile_ids: list[str]`
- can create the full tile pool
- can deal racks
- can draw a random tile
- validates the complete 106-tile set

### Board

- stores `melds: list[Meld]`
- supports adding or replacing meld lists

### Player

Fields:
- `id: str`
- `name: str | None`
- `initial_meld_met: bool`
- `rack: Rack`
- `joined: bool`

Behavior:
- `create_player()` generates the ID
- `update()` returns an updated player copy
- rack mutation helpers return new player objects

### GameState

Fields:
- `game_id: UUID`
- `game_name: str`
- `players: list[Player]`
- `current_player_index: int`
- `pool: Pool`
- `board: Board`
- `created_at: datetime`
- `updated_at: datetime`
- `status: GameStatus`
- `winner_player_id: str | None`
- internal `id: UUID`
- `num_players: int`

Creation helpers:
- `create_initialized_game(num_players)` creates a full game with pre-dealt seats
- `create_new_game(...)` creates a mostly empty game-state object used by tests

Copy/update helpers:
- `update_player()`
- `update_board()`
- `_copy_with()`

Integrity helper:
- `validate_tile_ownership()` checks that racks, pool, and board form a complete partition of the full tile set

## Actions

The action model is intentionally small:

- `PlayTilesAction(type="play_tiles", melds=list[Meld])`
- `DrawAction(type="draw")`
- `Turn(player_id, action)`

`PlayTilesAction.melds` is interpreted as the full board end-state after the move.

## Exceptions

Validation and game-state errors are defined in `exceptions.py`.

Important classes include:
- `InvalidNumberError`
- `InvalidMeldError`
- `JokerAssignmentError`
- `GameStateError`
- `GameFullError`
- `GameNotStartedError`
- `GameFinishedError`
- `NotPlayersTurnError`
- `PlayerNotInGameError`
- `InitialMeldNotMetError`
- `InvalidMoveError`
- `TileNotOwnedError`
- `PoolEmptyError`
- `InvalidBoardStateError`

## Invariants

The intended invariants are:
- the full game contains exactly 106 deterministic tile IDs
- rack tiles, board tiles, and pool tiles form a full partition of that set
- groups and runs are always valid melds after a turn completes
- the initial meld threshold is 30 points
- runs never wrap from 13 back to 1

One of these invariants is not fully enforced on play actions yet: board-tile conservation after board replacement. That gap is documented in `doc/CODE_REVIEW.md`.
