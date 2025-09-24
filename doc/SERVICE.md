# Game Service (Redis)

Service layer that provides persistence and concurrency control for multiplayer Rummikub games using Redis as the backend.

## Overview

The service layer acts as a bridge between the stateless game engine and persistent storage, providing:
- Game state persistence and retrieval
- Concurrency control for multiplayer games
- Game lifecycle management

## Redis Schema

### Key Naming Conventions

Simple key structure for storing game states:

```
rummikub:games:{game_id}                    # Game state (JSON)
rummikub:games:{game_id}:lock               # Game-level lock (STRING)
```

### Data Structures

#### 1. Game State (`rummikub:games:{game_id}`)
**Type**: JSON  
**TTL**: 24 hours for completed games, no expiry for active games  
**Content**: Serialized `GameState` object

```json
{
  "game_id": "uuid-string",
  "players": [
    {
      "id": "player-uuid",
      "name": "Player Name",
      "initial_meld_met": false,
      "rack": {
        "tile_ids": ["tile-uuid-1", "tile-uuid-2", ...]
      }
    }
  ],
  "current_player_index": 0,
  "pool": {
    "tile_ids": ["tile-uuid-x", "tile-uuid-y", ...]
  },
  "board": {
    "melds": [
      {
        "id": "meld-uuid",
        "kind": "GROUP",
        "tiles": ["tile-uuid-a", "tile-uuid-b", "tile-uuid-c"]
      }
    ]
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z",
  "status": "IN_PROGRESS",
  "winner_player_id": null,
  "num_players": 4
}
```

#### 2. Game Lock (`rummikub:games:{game_id}:lock`)
**Type**: STRING  
**TTL**: 5 seconds (auto-release on timeout)  
**Content**: Session ID of lock holder

Used for exclusive locking during game state updates.

## Concurrency Model

### Simple Locking Strategy

The service uses a simple lock-read-action-save-unlock pattern to handle concurrent game state modifications:

1. **Lock**: Acquire exclusive lock on game
2. **Read**: Read current game state from Redis
3. **Action**: Apply game engine operations
4. **Save**: Write updated game state to Redis
5. **Unlock**: Release the exclusive lock

If a lock is already held, the operation waits for the lock to be released.

### Lock Implementation

```python
def acquire_game_lock(game_id: str, session_id: str) -> bool:
    """Acquire exclusive lock on game for updates. Blocks until available."""
    lock_key = f"rummikub:games:{game_id}:lock"
    while True:
        acquired = redis.set(lock_key, session_id, nx=True, ex=5)
        if acquired:
            return True
        time.sleep(0.1)  # Wait before retry

def release_game_lock(game_id: str, session_id: str) -> bool:
    """Release lock if owned by session."""
    lock_key = f"rummikub:games:{game_id}:lock"
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    return redis.eval(lua_script, [lock_key], [session_id])
```

### Conflict Resolution

- **Lock contention**: Operations wait for lock release with automatic retry
- **Lock timeouts**: Very short TTL (5 seconds) ensures quick recovery from failures
- **Network failures**: Automatic lock cleanup prevents deadlocks

## Service API Contracts

### Core Service Interface

```python
@dataclass
class GameService:
    """Main service interface for game management."""
    
    # Game Lifecycle
    def create_game(self, num_players: int) -> GameState:
        """Create new game and return state."""
    
    def join_game(self, game_id: str, player_name: str) -> GameState:
        """Join game by game ID. Returns curated game state for the player.
        If player already joined, returns their current game view."""
    
    def get_game(self, game_id: str, player_name: str) -> GameState | None:
        """Retrieve curated game state for the specific player.
        Only shows the player's own rack, other players show rack count only."""
    
    def get_games(self) -> list[GameState]:
        """Retrieve list of all stored games."""
    
    # Game Actions
    def execute_turn(self, game_id: str, player_id: str, action: Action) -> GameState:
        """Execute player action (play tiles or draw). Includes player validation."""
```

### Exception Mapping

Service-specific exceptions that wrap domain exceptions:

```python
class ServiceError(Exception):
    """Base service layer exception."""

class GameNotFoundError(ServiceError):
    """Game ID not found in Redis."""

class ConcurrentModificationError(ServiceError):
    """Game modified by another player."""
```

## Game Management Flows

### Game Creation Flow

1. Service creates game via engine → `GameState`
2. Service persists game state to Redis with game_id as key
3. Return `GameState`

### Join Game Flow

1. Service calls join_game with game_id and player_name
2. If player already joined, identify player and return curated game state
3. If game already started, identify player by name and return curated game state
4. Otherwise, add player to game and return curated game state
5. Curated state shows only the player's rack, other players show rack count only

### Turn Execution Flow

1. Acquire game lock
2. Retrieve current game state
3. Execute action via engine (includes player validation)
4. Persist updated game state
5. Release game lock
6. Return updated curated `GameState`

## Persistence Strategy

### Data Consistency

- **Atomicity**: Use Redis transactions for multi-key updates
- **Durability**: Configure Redis persistence (AOF + RDB)
- **Lock safety**: Short TTL prevents deadlocks

### Memory Management

- **TTL Policy**: Completed games expire after 24 hours
- **Cleanup**: Automatic cleanup of expired games

## Implementation Notes

- **DI-Friendly**: Service accepts Redis client interface for testing
- **Synchronous**: All operations are synchronous for simplicity
- **Type Safety**: Full type annotations with proper generics
- **Error Handling**: Comprehensive exception hierarchy
- **Testing**: Use `fakeredis` for unit tests, real Redis for integration
- **Configuration**: Environment-based Redis connection settings
