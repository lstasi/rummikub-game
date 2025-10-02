# API Interface

REST API endpoints for the Rummikub game server, built with FastAPI. Provides game management, player actions, and real-time game state access.

## Overview

The API provides a stateless REST interface over the GameService layer, with automatic request/response validation, OpenAPI documentation, and comprehensive error handling.

### API Characteristics
- **HTTP/REST**: Standard REST patterns with JSON payloads
- **Stateless**: No server-side session management
- **Validation**: Automatic request/response validation via Pydantic models
- **Documentation**: Auto-generated OpenAPI spec at `/docs`
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Authentication**: None required for v1 (future versions may add API keys/OAuth)

## Base Configuration

```
Base URL: http://localhost:8090/api/v1
Content-Type: application/json
```

## Endpoints

### 1. Get Games List

**GET `/games`**

Retrieve a list of all available games.

**Response: 200 OK**
```json
{
  "games": [
    {
      "game_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "waiting_for_players",
      "num_players": 2,
      "players": [
        {
          "id": "player-123",
          "name": "Alice",
          "initial_meld_met": false,
          "rack_size": 14
        }
      ],
      "current_player_index": 0,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:05:00Z"
    }
  ]
}
```

### 2. Create Game

**POST `/games`**

Create a new game with specified number of players.

**Request Body**
```json
{
  "num_players": 4
}
```

**Response: 201 Created**
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "waiting_for_players",
  "num_players": 4,
  "players": [],
  "current_player_index": 0,
  "pool_size": 106,
  "board": {
    "melds": []
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "winner_player_id": null
}
```

**Errors**
- `400 Bad Request`: Invalid num_players (must be 2-4)

### 3. Join Game

**POST `/games/{game_id}/join`**

Join an existing game as a player.

**Path Parameters**
- `game_id`: UUID string of the game to join

**Request Body**
```json
{
  "player_name": "Alice"
}
```

**Response: 200 OK**
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "num_players": 4,
  "players": [
    {
      "id": "player-123",
      "name": "Alice", 
      "initial_meld_met": false,
      "rack": {
        "tiles": ["7ra", "12kb", "ja", ...]
      }
    },
    {
      "id": "player-456",
      "name": "Bob",
      "initial_meld_met": false,
      "rack_size": 14
    }
  ],
  "current_player_index": 0,
  "pool_size": 78,
  "board": {
    "melds": []
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "winner_player_id": null
}
```

**Notes**
- Response shows full rack for the joining player, only rack_size for others
- If player already joined, returns current game state for that player
- Game starts automatically when all player slots are filled

**Errors**
- `404 Not Found`: Game not found
- `409 Conflict`: Game is full or already completed

### 4. Get Game State

**GET `/games/{game_id}/players/{player_name}`**

Get current game state from the perspective of a specific player.

**Path Parameters**
- `game_id`: UUID string of the game
- `player_name`: Name of the player requesting the state

**Response: 200 OK**
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "num_players": 4,
  "players": [
    {
      "id": "player-123",
      "name": "Alice",
      "initial_meld_met": false,
      "rack": {
        "tiles": ["7ra", "12kb", "ja", ...]
      }
    },
    {
      "id": "player-456", 
      "name": "Bob",
      "initial_meld_met": true,
      "rack_size": 10
    }
  ],
  "current_player_index": 1,
  "pool_size": 45,
  "board": {
    "melds": [
      {
        "id": "meld-789",
        "kind": "group",
        "tiles": ["7ra", "7kb", "7bo"]
      }
    ]
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:15:00Z",
  "winner_player_id": null
}
```

**Notes**
- Shows full rack only for the requesting player
- Other players show only rack_size for privacy

**Errors**
- `404 Not Found`: Game not found or player not in game

### 5. Execute Turn - Play Tiles

**POST `/games/{game_id}/players/{player_id}/actions/play`**

Execute a play tiles action (place new melds and/or rearrange existing ones).

**Path Parameters**
- `game_id`: UUID string of the game
- `player_id`: UUID string of the player taking the action

**Request Body**
```json
{
  "melds": [
    {
      "id": "meld-new-1",
      "kind": "group",
      "tiles": ["7ra", "7kb", "7bo"]
    },
    {
      "id": "meld-existing-789", 
      "kind": "run",
      "tiles": ["10ka", "11ka", "12ka", "13ka"]
    }
  ]
}
```

**Response: 200 OK**
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "players": [...],
  "current_player_index": 2,
  "pool_size": 45,
  "board": {
    "melds": [
      {
        "id": "meld-new-1",
        "kind": "group", 
        "tiles": ["7ra", "7kb", "7bo"]
      },
      {
        "id": "meld-existing-789",
        "kind": "run",
        "tiles": ["10ka", "11ka", "12ka", "13ka"]
      }
    ]
  },
  "updated_at": "2024-01-01T12:16:00Z",
  "winner_player_id": "player-123"
}
```

**Notes**
- `melds` array represents the complete board state after the action
- Engine validates tile ownership, meld validity, and initial meld requirements
- Turn advances automatically after successful play
- Game status changes to "completed" if player wins

**Errors**
- `400 Bad Request`: Invalid meld formations or action structure
- `403 Forbidden`: Not player's turn or player not in game  
- `404 Not Found`: Game not found
- `422 Unprocessable Entity`: Rule violations (see error details below)

### 6. Execute Turn - Draw Tile

**POST `/games/{game_id}/players/{player_id}/actions/draw`**

Draw a tile from the pool.

**Path Parameters**  
- `game_id`: UUID string of the game
- `player_id`: UUID string of the player taking the action

**Request Body**
```json
{}
```

**Response: 200 OK**
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000", 
  "status": "in_progress",
  "players": [
    {
      "id": "player-123",
      "name": "Alice",
      "initial_meld_met": false,
      "rack": {
        "tiles": ["7ra", "12kb", "ja", "3bo", ...]
      }
    }
  ],
  "current_player_index": 1,
  "pool_size": 44,
  "board": {
    "melds": [...]
  },
  "updated_at": "2024-01-01T12:17:00Z"
}
```

**Notes**
- Adds one random tile from pool to player's rack
- Turn advances automatically after successful draw

**Errors**
- `400 Bad Request`: Pool is empty
- `403 Forbidden`: Not player's turn or player not in game
- `404 Not Found`: Game not found

## Data Models

### GameState Schema

```json
{
  "game_id": "string (UUID)",
  "status": "waiting_for_players" | "in_progress" | "completed",
  "num_players": "integer (2-4)",
  "players": ["PlayerState"],
  "current_player_index": "integer",
  "pool_size": "integer",
  "board": "BoardState",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)", 
  "winner_player_id": "string (UUID) | null"
}
```

### PlayerState Schema

```json
{
  "id": "string (UUID)",
  "name": "string",
  "initial_meld_met": "boolean",
  "rack": "RackState | null",
  "rack_size": "integer | null"
}
```

**Notes**
- `rack` is populated only for the requesting player
- `rack_size` is populated for other players (privacy)

### RackState Schema

```json
{
  "tiles": ["string (tile IDs)"]
}
```

### BoardState Schema

```json
{
  "melds": ["MeldState"]
}
```

### MeldState Schema

```json
{
  "id": "string (UUID)",
  "kind": "group" | "run", 
  "tiles": ["string (tile IDs)"]
}
```

### Tile ID Format

- **Numbered tiles**: `{number}{color_code}{copy}`
  - Examples: `7ra` (Red 7 copy A), `13kb` (Black 13 copy B)
- **Jokers**: `j{copy}`
  - Examples: `ja` (Joker A), `jb` (Joker B)

**Color Codes**
- `k` = black, `r` = red, `b` = blue, `o` = orange

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context when applicable"
    }
  }
}
```

### Error Codes and HTTP Status Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request body or parameters |
| 400 | `INVALID_NUM_PLAYERS` | num_players not in range 2-4 |
| 400 | `POOL_EMPTY` | Cannot draw from empty pool |
| 403 | `NOT_PLAYERS_TURN` | Action attempted by wrong player |
| 403 | `PLAYER_NOT_IN_GAME` | Player not found in game |
| 404 | `GAME_NOT_FOUND` | Game ID does not exist |
| 409 | `GAME_FULL` | Cannot join, game already has max players |
| 409 | `GAME_FINISHED` | Cannot perform actions on completed game |
| 422 | `INVALID_MELD` | Meld violates game rules |
| 422 | `INITIAL_MELD_NOT_MET` | First play must total ≥30 points |
| 422 | `INVALID_MOVE` | Move violates game rules |
| 422 | `TILE_NOT_OWNED` | Player doesn't own specified tiles |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 503 | `CONCURRENT_MODIFICATION` | Game state changed during operation |

### Example Error Responses

**Invalid num_players**
```json
{
  "error": {
    "code": "INVALID_NUM_PLAYERS",
    "message": "Number of players must be between 2 and 4",
    "details": {
      "num_players": 5
    }
  }
}
```

**Invalid meld**
```json
{
  "error": {
    "code": "INVALID_MELD", 
    "message": "Group contains duplicate colors",
    "details": {
      "meld_id": "meld-789",
      "reason": "color-duplication",
      "tiles": ["7ra", "7ra", "7kb"]
    }
  }
}
```

**Not player's turn**
```json
{
  "error": {
    "code": "NOT_PLAYERS_TURN",
    "message": "It is not your turn",
    "details": {
      "current_player": "player-456",
      "requesting_player": "player-123"
    }
  }
}
```

## Implementation Notes

### FastAPI Integration

- Uses Pydantic v2 models for request/response validation
- Automatic OpenAPI schema generation at `/docs` and `/redoc`
- Dependency injection for GameService (Redis client)
- Exception handlers for domain exceptions → HTTP responses
- CORS enabled for development (configurable)

### Request/Response Processing

- All JSON payloads use snake_case consistently
- UUID fields accept string format and validate automatically
- Timestamps in ISO 8601 format (UTC)
- Game state responses curated based on requesting player
- Deterministic tile ID format for stable client-side caching

### Validation Strategy

- **Input validation**: Pydantic models with custom validators
- **Business rules**: Delegated to GameEngine and GameService layers
- **Response filtering**: Player-specific game state curation
- **Error mapping**: Domain exceptions mapped to appropriate HTTP status codes

### Performance Considerations

- Stateless design enables horizontal scaling
- Redis handles concurrent game state modifications
- Response curation minimizes payload size
- Structured logging for request tracing and debugging

### Future Extensions

- WebSocket support for real-time game updates
- Authentication/authorization (API keys, OAuth2)
- Rate limiting per player/IP
- Game replay and history endpoints
- Spectator mode for completed games
