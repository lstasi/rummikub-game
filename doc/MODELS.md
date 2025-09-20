# Domain Models

This document defines the domain model for the Rummikub game, derived from `RUMMIKUB_RULES.md`. These definitions guide the implementation in `src/rummikub/models/` and are the source of truth for validation logic and serialization contracts.

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
