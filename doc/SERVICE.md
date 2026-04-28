# Game Service

The service layer in `src/rummikub/service/game_service.py` persists `GameState` objects to Redis and serializes access to per-game updates.

## Responsibilities

- Create, load, update, and delete games in Redis
- Bridge the stateless engine with persistent storage
- Return player-curated views that hide other players' racks
- Apply a simple lock around state-changing operations

## Redis Keys

The implementation uses two key shapes:

```text
rummikub:games:{game_id}
rummikub:games:{game_id}:lock
```

### Game State Key

- Value: JSON string produced from `dataclasses.asdict()` plus manual UUID and datetime conversion
- Expiry: no TTL for active games, 24 hours for completed games

### Lock Key

- Value: service `session_id`
- Expiry: 5 seconds
- Purpose: serialize concurrent updates on a single game

## Public Service Methods

```python
GameService.create_game(num_players: int) -> GameState
GameService.join_game(game_id: str, player_name: str) -> GameState
GameService.get_game(game_id: str, player_name: str) -> GameState | None
GameService.get_games() -> list[GameState]
GameService.execute_turn(game_id: str, player_id: str, action: Action) -> GameState
GameService.delete_game(game_id: str) -> None
```

Behavior notes:
- `join_game()` returns the joining player's curated view.
- Rejoining by name returns the existing player's curated view instead of creating a duplicate player.
- `execute_turn()` accepts either `PlayTilesAction` or `DrawAction`.

## Serialization Model

The service stores full `GameState` objects, not API response shapes.

Important serialized fields include:
- `game_id`
- `game_name`
- `players`
- `current_player_index`
- `pool`
- `board`
- `created_at`
- `updated_at`
- `status`
- `winner_player_id`
- internal `id`
- `num_players`

Deserialization reconstructs:
- `Player`
- `Rack`
- `Pool`
- `Board`
- `Meld`
- `GameState`

## Player-Curated Views

The service hides other players' rack contents by rebuilding the player list:

- The requesting player keeps the full rack.
- Other players get an empty rack in the curated state.
- The API response layer then exposes `rack_size` from the original state when available.

This keeps Redis storage full-fidelity while still supporting privacy at the response layer.

## Locking Model

The lock implementation is intentionally simple:

1. Try `SET key value NX EX 5`.
2. Retry every 100 ms for up to 50 attempts.
3. On success, execute the update.
4. Release with a Lua compare-and-delete script.
5. Fall back to manual ownership check if Lua is unavailable.

If acquisition fails after 50 attempts, the service raises `ConcurrentModificationError`.

## Data Flow

### Create Game

1. Engine creates a new `GameState`.
2. Service serializes and stores it.
3. API may then immediately call `join_game()` for the creator.

### Join Game

1. Acquire lock.
2. Load game.
3. If the player already exists by name, return that view.
4. Otherwise join through the engine and persist the update.
5. Return the curated player view.

### Execute Turn

1. Acquire lock.
2. Load game.
3. Execute the action through the engine.
4. Persist the new state.
5. Return a curated player view.

## Current Limitations

- `get_games()` uses Redis `KEYS`, which is acceptable for a small MVP but not ideal for large keyspaces.
- The lock is a coarse per-game spin lock and is not suitable for high-contention workloads.
- The service trusts the engine for board integrity; stronger post-action partition validation is still needed.

See `doc/CODE_REVIEW.md` for the priority fixes.
