# Game Service (Redis)

Service layer that provides persistence, concurrency control, and session management for multiplayer Rummikub games using Redis as the backend.

## Overview

The service layer acts as a bridge between the stateless game engine and persistent storage, providing:
- Game state persistence and retrieval
- Concurrency control for multiplayer games
- Session management with invite codes
- Player connection tracking
- Game lifecycle management

## Redis Schema

### Key Naming Conventions

All Redis keys follow a hierarchical pattern for organization and efficient querying:

```
rummikub:games:{game_id}                    # Game state (JSON)
rummikub:games:{game_id}:lock               # Game-level lock (STRING)
rummikub:games:{game_id}:players            # Player connection status (HASH) 
rummikub:games:{game_id}:tiles              # Tile instances (HASH)

rummikub:invites:{invite_code}              # Invite code mapping (STRING -> game_id)
rummikub:player_sessions:{session_id}       # Session to player/game mapping (HASH)

rummikub:game_index:waiting                 # Games waiting for players (SET)
rummikub:game_index:active                  # Games in progress (SET)
rummikub:game_index:completed               # Completed games (SET with expiry)
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
**TTL**: 30 seconds (auto-release on timeout)  
**Content**: Session ID of lock holder

Used for optimistic locking during game state updates.

#### 3. Player Connections (`rummikub:games:{game_id}:players`)
**Type**: HASH  
**TTL**: No expiry (cleaned up with game)  
**Fields**: `player_id -> last_seen_timestamp`

Tracks which players are currently connected/active.

#### 4. Tile Instances (`rummikub:games:{game_id}:tiles`)
**Type**: HASH  
**TTL**: No expiry (cleaned up with game)  
**Fields**: `tile_id -> tile_json`

Stores individual tile instances for efficient lookup:
```json
{
  "tile-uuid-1": {
    "id": "tile-uuid-1",
    "kind": {
      "type": "numbered",
      "number": 7,
      "color": "red"
    }
  },
  "tile-uuid-2": {
    "id": "tile-uuid-2", 
    "kind": {
      "type": "joker"
    }
  }
}
```

#### 5. Invite Codes (`rummikub:invites:{invite_code}`)
**Type**: STRING  
**TTL**: 1 hour  
**Content**: `game_id`

6-character alphanumeric codes for easy game joining.

#### 6. Player Sessions (`rummikub:player_sessions:{session_id}`)
**Type**: HASH  
**TTL**: 4 hours  
**Fields**: 
```
player_id: "player-uuid"
game_id: "game-uuid"
player_name: "Display Name"
connected_at: "2024-01-01T12:00:00Z"
```

## Concurrency Model

### Optimistic Locking Strategy

The service uses optimistic locking to handle concurrent game state modifications:

1. **Read Phase**: Client reads current game state
2. **Lock Acquisition**: Acquire exclusive lock with short TTL (30s)
3. **Validation**: Verify game state hasn't changed since read
4. **Update**: Apply changes atomically
5. **Lock Release**: Release lock immediately after update

### Lock Implementation

```python
async def acquire_game_lock(game_id: str, session_id: str) -> bool:
    """Acquire exclusive lock on game for updates."""
    lock_key = f"rummikub:games:{game_id}:lock"
    acquired = await redis.set(lock_key, session_id, nx=True, ex=30)
    return acquired

async def release_game_lock(game_id: str, session_id: str) -> bool:
    """Release lock if owned by session."""
    lock_key = f"rummikub:games:{game_id}:lock"
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    return await redis.eval(lua_script, [lock_key], [session_id])
```

### Conflict Resolution

- **Read conflicts**: Return current state, let client retry
- **Write conflicts**: Fail fast with `ConcurrentModificationError`
- **Lock timeouts**: Automatic cleanup, but log for monitoring
- **Network partitions**: Use heartbeat to detect disconnected players

## Service API Contracts

### Core Service Interface

```python
@dataclass
class GameService:
    """Main service interface for game management."""
    
    # Game Lifecycle
    async def create_game(self, num_players: int, creator_session: str) -> tuple[GameState, str]:
        """Create new game and return state + invite code."""
    
    async def join_game(self, invite_code: str, player_name: str, session_id: str) -> GameState:
        """Join game via invite code."""
    
    async def get_game(self, game_id: str) -> GameState | None:
        """Retrieve current game state."""
    
    async def start_game(self, game_id: str, session_id: str) -> GameState:
        """Start game if all players joined."""
    
    # Game Actions
    async def execute_turn(self, game_id: str, player_id: str, action: Action, session_id: str) -> GameState:
        """Execute player action (play tiles or draw)."""
    
    async def get_current_player(self, game_id: str) -> str:
        """Get ID of player whose turn it is."""
    
    # Session Management  
    async def create_session(self, player_name: str) -> str:
        """Create new player session."""
    
    async def get_session(self, session_id: str) -> PlayerSession | None:
        """Retrieve session information."""
    
    async def update_player_heartbeat(self, game_id: str, player_id: str) -> None:
        """Update player's last-seen timestamp."""
    
    # Game Discovery
    async def list_waiting_games(self) -> list[GameState]:
        """List games waiting for players."""
```

### Exception Mapping

Service-specific exceptions that wrap domain exceptions:

```python
class ServiceError(Exception):
    """Base service layer exception."""

class GameNotFoundError(ServiceError):
    """Game ID not found in Redis."""

class InvalidInviteCodeError(ServiceError): 
    """Invite code expired or invalid."""

class ConcurrentModificationError(ServiceError):
    """Game modified by another player."""

class SessionExpiredError(ServiceError):
    """Player session no longer valid."""

class PlayerDisconnectedError(ServiceError):
    """Player connection lost."""
```

## Session and Invite Flows

### Game Creation Flow

1. Player creates session → `session_id`
2. Service creates game via engine → `GameState`
3. Service persists game state to Redis
4. Service generates 6-character invite code
5. Service stores invite mapping: `invite_code → game_id`
6. Service adds game to waiting index
7. Return `GameState` + `invite_code`

### Join Game Flow

1. Player provides invite code + display name
2. Service validates invite code exists and not expired
3. Service retrieves game state
4. Service validates game accepts more players
5. Service creates player session
6. Service updates game via engine (`join_game`)
7. Service persists updated game state
8. Service adds player to connection tracking
9. Return updated `GameState`

### Turn Execution Flow

1. Validate session and player permissions
2. Acquire game lock for current player
3. Retrieve current game state
4. Validate it's player's turn
5. Execute action via engine
6. Persist updated game state
7. Update player heartbeat
8. Release game lock
9. Broadcast state change to all players
10. Return updated `GameState`

### Disconnect Handling

- **Heartbeat mechanism**: Players send periodic heartbeats
- **Timeout detection**: Mark players inactive after 2 minutes
- **Game suspension**: Pause game if any player disconnects
- **Reconnection**: Allow players to rejoin with session ID
- **Abandonment**: End game if player absent > 10 minutes

## Persistence Strategy

### Data Consistency

- **Atomicity**: Use Redis transactions for multi-key updates
- **Durability**: Configure Redis persistence (AOF + RDB)
- **Backup**: Regular snapshots of game states
- **Recovery**: Replay mechanism for incomplete games

### Memory Management

- **TTL Policy**: Completed games expire after 24 hours
- **Cleanup**: Background job removes abandoned games
- **Compression**: Use JSON compression for large game states
- **Indexing**: Maintain efficient lookup indices

### Monitoring Points

- Game creation/completion rates
- Average game duration
- Player connection stability
- Lock contention metrics
- Redis memory usage
- Error rates by exception type

## Implementation Notes

- **DI-Friendly**: Service accepts Redis client interface for testing
- **Async/Await**: All operations are async for high concurrency
- **Type Safety**: Full type annotations with proper generics
- **Error Handling**: Comprehensive exception hierarchy
- **Logging**: Structured logging for observability
- **Testing**: Use `fakeredis` for unit tests, real Redis for integration
- **Configuration**: Environment-based Redis connection settings
