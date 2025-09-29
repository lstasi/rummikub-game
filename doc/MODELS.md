# Domain Models

This document defines the domain model for the Rummikub game, derived from `RUMMIKUB_RULES.md`. These definitions guide implementation in `src/rummikub/models/` and are the source of truth for validation logic and serialization contracts.

## Overview of Entities

- Color: one of {black, red, blue, orange}
- Tile: numbered tile (1–13) with a Color; two copies per (number, color)
- Joker: special tile that can represent any numbered tile contextually
- Meld: either a Group or a Run
  - Group: 3–4 tiles with the same number and all distinct colors
  - Run: 3+ tiles with consecutive numbers and the same color
- Rack: multiset of tiles held by a player (hidden from others)
- Pool: multiset of face-down tiles available to draw
- Board: set of Melds visible to all players
- Player: unique id, name (optional), and a Rack
- GameState: has a Pool, a list of Players, and a Board; also tracks turn order and per-player status (e.g., initial meld met)
- Turn and Action: a turn encapsulates exactly one action (either play tiles or draw)

## Implementation Notes

- Uses Python dataclasses for simplicity since game rules are fixed and won't change
- UUIDv4 for tile and meld identifiers
- Maintain tile order in runs; for groups, order doesn't matter but preserve stable ordering for deterministic serialization
- Basic validation in `__post_init__` methods; complex validation moved to service layer
- Simple JSON serialization utilities provided in base module

## Package Structure

The implementation is organized as follows:
- `base.py`: Common utilities for ID generation and JSON serialization
- `tiles.py`: Color enum, tile validation models (NumberedTile, JokerTile), and TileUtils static helpers
- `melds.py`: Meld models with integrated validation
- `game.py`: Game state models (Player, Rack, Pool, Board, GameState)
- `actions.py`: Turn and action models
- `exceptions.py`: Domain-specific exception classes

## Identifiers and Multiplicity

- Each physical tile is represented by a unique string ID that encodes its properties:
  - Numbered tiles: "{number}{color_code}{copy}" (e.g., "7ra" = Red 7 copy A)
  - Joker tiles: "j{copy}" (e.g., "ja" = Joker copy A)
  - Color codes: 'k'=black, 'r'=red, 'b'=blue, 'o'=orange
  - Copy identifiers: 'a' and 'b' (for the two copies of each tile)
- Validation models for tile structure:
  - NumberedTile: (number: int 1–13, color: Color) - used for validation only
  - JokerTile: special tile marker - used for validation only
- Static utilities provided by TileUtils class for working with tile ID strings

## Invariants and Validation Rules

1) Tile domain
	- number in [1, 13]
	- color in {black, red, blue, orange}

2) Group meld
	- size ∈ {3, 4}
	- all tiles same number
	- all colors distinct
	- jokers allowed; each joker substitutes for the missing color of that number

3) Run meld
	- size ≥ 3
	- all tiles same color
	- numbers form a strictly increasing consecutive sequence
	- jokers allowed; each joker substitutes the required missing number in sequence
	- boundaries: cannot wrap (i.e., 12-13-1 invalid)

4) Joker rules
	- A joker takes the value (number, color) implied by the meld and its position.
	- Retrieving a joker is possible by replacing it with the actual tile and the joker must be used within the same turn.

5) Board validity
	- After any turn completes, all melds on the board must be valid (Groups or Runs) with joker assignments resolved.
	- Rearrangements are permitted only if the end state is valid.

6) Initial meld
	- A player must first place meld(s) whose total face value ≥ 30 before adding to or rearranging existing board melds.
	- Jokers count as the value of the tile they represent for initial meld computation.

## Data Structures (Logical Design)

- Color: enum {BLACK, RED, BLUE, ORANGE}
- TileKind: union of NumberedTile(number: int, color: Color) | JokerTile (used for validation only)
- Tile representation: string ID directly (no wrapper object)
  - Format: numbered="7ra" (Red 7 copy A), joker="ja" (Joker copy A)
  - TileUtils provides static methods for parsing and working with tile IDs
- MeldKind: GROUP | RUN
- Meld:
  - kind: MeldKind  
  - tiles: list of tile ID strings (position matters for runs, groups use deterministic color ordering)
  - id: deterministic ID generated from sorted tile IDs (groups: Black-Red-Blue-Orange order, runs: sequence order)
  - validate(): validates meld structure with integrated joker assignment
  - get_value(): calculates meld point value with joker resolution
- Rack: { tile_ids: list[string] }
- Pool: list[string]
- Board: list of Melds
- Player: { id: str, name?: str, initial_meld_met: bool, rack: Rack }
- Turn: { player_id: str, action: Action }
 - Action (discriminated union by field `type`):
  - { type: "play_tiles", melds: list[Meld] }
    // melds represent the full board end-state after playing/rearranging tiles this turn.
    // the engine must validate that all melds are legal and all moved tiles come from the player's rack or board.
  - { type: "draw" }

Note: Actions are limited to two types: type = "play_tiles" (may include rearrangements and joker retrieval within the single action) or type = "draw".

## Serialization Requirements

- All entities must serialize to JSON deterministically with stable tile IDs.
- Simple dataclass-based approach with utility functions:
  - Color as string enum: "black" | "red" | "blue" | "orange"
  - Tiles are represented directly as string IDs: "7ra", "12ko", "ja"
    - No nested tile objects - just the ID string which encodes all tile information
    - Use TileUtils static methods to extract number, color, joker status from ID
  - Meld: { id: string, kind: "group"|"run", tiles: string[] }
    - Meld IDs are deterministic: sorted tile IDs joined with "-" (groups by color order, runs by sequence)
    - Examples: "7ka-7ra-7ba" (group), "5ra-6ra-7ra" (run)
  - Board: { melds: Meld[] }
  - Player: { id: string, name?: string, initial_meld_met: boolean, rack: Rack }
  - GameState: see below

## GameState

Fields:
- game_id: string (UUID)
- players: list[Player] with turn order by index
- current_player_index: int
- pool: list[string] (face-down tile IDs)
- board: list[Meld]
- created_at, updated_at: timestamps (UTC ISO8601)
- status: enum { WAITING_FOR_PLAYERS, IN_PROGRESS, COMPLETED }
- winner_player_id?: string

Constraints:
- current_player_index ∈ [0, len(players)-1] when IN_PROGRESS
- winner_player_id set only when COMPLETED
- Tile ownership partition: players' racks + board tiles + pool form a partition of all tiles

## Derived Utilities

Implement as pure functions within models:
- is_valid_group(tiles)
- is_valid_run(tiles)
- assign_jokers_in_group(tiles)
- assign_jokers_in_run(tiles)
- meld_value(meld): sum of face values (joker -> represented value)
- initial_meld_total(melds): int

## Edge Cases to Cover in Tests

- Group with duplicate colors (invalid)
- Run with non-consecutive sequence (invalid)
- Run with mixed colors (invalid)
- Jokers filling gaps at either end and middle of runs
- Jokers in groups ensuring color uniqueness
- Initial meld value computation with jokers
- Serialization round-trip preserving tile ids and joker identity

## Error Taxonomy (for validation)

- InvalidColorError, InvalidNumberError
- InvalidMeldError (with reason: size, color-duplication, non-consecutive, mixed-colors)
- JokerAssignmentError (ambiguous or impossible)


## Package Structure

The implementation is organized as follows:
- `base.py`: Common base classes and utility types
- `tiles.py`: Color enum and tile-related models (TileKind, TileInstance)
- `melds.py`: Meld models with validation logic
- `game.py`: Game state models (Player, Rack, Pool, Board, GameState)
- `actions.py`: Turn and action models
- `validators.py`: Pure validation functions and utilities
- `exceptions.py`: Domain-specific exception classese implementation in `src/rummikub/models/` and are the source of truth for validation logic and serialization contracts.

## Overview of Entities

- Color: one of {black, red, blue, orange}
- Tile: numbered tile (1–13) with a Color; two copies per (number, color)
- Joker: special tile that can represent any numbered tile contextually
- Meld: either a Group or a Run
  - Group: 3–4 tiles with the same number and all distinct colors
  - Run: 3+ tiles with consecutive numbers and the same color
- Rack: multiset of tiles held by a player (hidden from others)
- Pool: multiset of face-down tiles available to draw
- Board: set of Melds visible to all players
- Player: unique id, name (optional), and a Rack
- GameSate: has a Pool, a list of Players, and a Board; also tracks turn order and per-player status (e.g., initial meld met)
- Turn and Action: a turn encapsulates exactly one action (either play tiles or draw)

## Identifiers and Multiplicity

- Each physical tile instance should have a stable unique id (UUID v4) to distinguish duplicates (e.g., two copies of Red 7).
- Logical tiles are described by kind:
  - NumberedTile: (number: int 1–13, color: Color)
  - JokerTile

## Invariants and Validation Rules

1) Tile domain
	- number in [1, 13]
	- color in {black, red, blue, orange}

2) Group meld
	- size ∈ {3, 4}
	- all tiles same number
	- all colors distinct
	- jokers allowed; each joker substitutes for the missing color of that number

3) Run meld
	- size ≥ 3
	- all tiles same color
	- numbers form a strictly increasing consecutive sequence
	- jokers allowed; each joker substitutes the required missing number in sequence
	- boundaries: cannot wrap (i.e., 12-13-1 invalid)

4) Joker rules
	- A joker takes the value (number, color) implied by the meld and its position.
	- Retrieving a joker is possible by replacing it with the actual tile and the joker must be used within the same turn.

5) Board validity
	- After any turn completes, all melds on the board must be valid (Groups or Runs) with joker assignments resolved.
	- Rearrangements are permitted only if the end state is valid.

6) Initial meld
	- A player must first place meld(s) whose total face value ≥ 30 before adding to or rearranging existing board melds.
	- Jokers count as the value of the tile they represent for initial meld computation.

## Data Structures (Logical Design)

- Color: enum {BLACK, RED, BLUE, ORANGE}
- TileKind: union of NumberedTile(number: int, color: Color) | Joker
- TileInstance: { id: UUID, kind: TileKind }
- MeldKind: GROUP | RUN
- Meld:
  - kind: MeldKind
  - tiles: ordered list of TileInstance ids (ordered for runs; order not significant for groups but retained for simplicity)
  - derived (runtime): resolved logical assignment for jokers
- Rack: { owner_player_id: str, tile_ids: multiset[UUID] }
- Pool: multiset[UUID]
- Board: list of Melds
- Player: { id: str, name?: str, initial_meld_met: bool, rack: Rack }
- Turn: { player_id: str, action: Action }
 - Action (discriminated union by field `type`):
  - { type: "play_tiles", melds: list[Meld] }
    // melds represent the full board end-state after playing/rearranging tiles this turn.
    // the engine must validate that all melds are legal and all moved tiles come from the player's rack or board.
  - { type: "draw" }

Note: Actions are limited to two types: type = "play_tiles" (may include rearrangements and joker retrieval within the single action) or type = "draw".

## Serialization Requirements

- All entities must serialize to JSON deterministically with stable ids.
- Suggested wire schema (Pydantic v2):
  - Color as string enum: "black" | "red" | "blue" | "orange"
  - Tile: { id: string-uuid, kind: { type: "numbered", number: int, color: Color } | { type: "joker" } }
  - Meld: { id: string-uuid, kind: "group"|"run", tiles: string-uuid[] }
  - Board: { melds: Meld[] }
	- Player: { id: string, name?: string, initial_meld_met: boolean, rack: Rack }
	- GameSate: see below

## GameSate

Fields:
- game_id: string (UUID)
- players: list[Player] with turn order by index
- current_player_index: int
- pool: list[string-uuid] (face-down tiles)
- board: list[Meld]
- created_at, updated_at: timestamps (UTC ISO8601)
- status: enum { WAITING_FOR_PLAYERS, IN_PROGRESS, COMPLETED }
- winner_player_id?: string

Constraints:
- current_player_index ∈ [0, len(players)-1] when IN_PROGRESS
- winner_player_id set only when COMPLETED
- Tile ownership partition: players' racks + board tiles + pool form a partition of all tiles

## Derived Utilities

Implement as pure functions within models:
- is_valid_group(tiles)
- is_valid_run(tiles)
- assign_jokers_in_group(tiles)
- assign_jokers_in_run(tiles)
- meld_value(meld): sum of face values (joker -> represented value)
- initial_meld_total(melds): int

## Edge Cases to Cover in Tests

- Group with duplicate colors (invalid)
- Run with non-consecutive sequence (invalid)
- Run with mixed colors (invalid)
- Jokers filling gaps at either end and middle of runs
- Jokers in groups ensuring color uniqueness
- Initial meld value computation with jokers
- Serialization round-trip preserving tile ids and joker identity

## Error Taxonomy (for validation)

- InvalidColorError, InvalidNumberError
- InvalidMeldError (with reason: size, color-duplication, non-consecutive, mixed-colors)
- JokerAssignmentError (ambiguous or impossible)

## Implementation Notes

- Prefer Pydantic models for validation and JSON I/O; dataclasses if simpler.
- Use UUIDv4 for tile and meld identifiers.
- Maintain tile order in runs; for groups, order doesn’t matter but preserve stable ordering for deterministic serialization.

---

## UPDATED: New Tile ID System  

**Replaced UUIDs with human-readable deterministic IDs for tiles:**

### Format
- **Numbered tiles**: `{number}{color_code}{copy}`
  - Examples: `7ra` (Red 7 copy A), `13kb` (Black 13 copy B)
- **Jokers**: `j{copy}`
  - Examples: `ja` (Joker A), `jb` (Joker B)

### Color Codes
- `k` = black
- `r` = red  
- `b` = blue
- `o` = orange

(Lowercase to avoid confusion between 'O' and '0')

### Benefits
- **Human-readable**: `7ra` vs `f47ac10b-58cc-4372-a567-0e02b2c3d479`
- **Deterministic**: Same tiles always get same IDs
- **Sortable**: Natural ordering by number, color, copy
- **Compact**: 3-4 characters vs 36 for UUID
- **Debug-friendly**: Easy to identify tiles in logs and tests

### Implementation Details
- Pool creation generates exactly 106 tiles: 104 numbered (2×13×4) + 2 jokers
- All tiles have predictable, stable IDs for reproducible testing
- Backward compatibility maintained: existing test code continues to work
- Factory methods: `TileInstance.create_numbered_tile()`, `TileInstance.create_joker_tile()`
- Meld IDs still use UUIDs for cross-session uniqueness
