# API Interface

This document describes the FastAPI contract currently exposed by `src/rummikub/api/main.py`.

## Base Configuration

- Base URL: `http://localhost:8090/api/v1`
- OpenAPI docs: `http://localhost:8090/docs`
- Content type: `application/json`

## Authentication

The API currently uses HTTP Basic Auth for game discovery and join flows.

- Username: player name
- Password: accepted but not validated

Example header:

```text
Authorization: Basic QWxpY2U6cGFzc3dvcmQ=
```

### Endpoints Requiring Basic Auth

- `GET /games`
- `GET /games/my-games`
- `POST /games`
- `POST /games/{game_id}/players`

### Endpoints Without Caller Authentication

- `GET /games/{game_id}/players/{player_id}`
- `POST /games/{game_id}/players/{player_id}/actions/play`
- `POST /games/{game_id}/players/{player_id}/actions/draw`
- `DELETE /games/{game_id}`
- `GET /health`

This is a known security problem, not a recommended design. See `doc/CODE_REVIEW.md`.

## Response Shape

Most game endpoints return the same `GameStateResponse` payload.

```json
{
  "game_id": "uuid-string",
  "game_name": "Battle of Tokyo",
  "status": "waiting_for_players",
  "num_players": 4,
  "players": [
    {
      "id": "player-uuid",
      "name": "Alice",
      "initial_meld_met": false,
      "rack": {
        "tiles": ["7ra", "12kb", "ja"]
      },
      "rack_size": null
    }
  ],
  "current_player_index": 0,
  "pool_size": 50,
  "board": {
    "melds": []
  },
  "created_at": "2026-04-28T12:00:00",
  "updated_at": "2026-04-28T12:00:00",
  "winner_player_id": null
}
```

Notes:
- Only joined players are included in `players`.
- The requesting player gets `rack`; other players get `rack_size`.
- `game_name` is generated server-side.
- `winner_player_id` exists in the schema but is not reliably populated yet.

## Endpoints

### GET /health

Health endpoint.

Response:

```json
{
  "status": "healthy"
}
```

### GET /games

List games visible to the authenticated player.

Behavior:
- Requires Basic Auth.
- Excludes games where the authenticated player has already joined.
- Accepts optional `status` query parameter.
- Invalid `status` values are ignored and the full result set is returned.

Example:

```http
GET /api/v1/games?status=waiting_for_players
```

### GET /games/my-games

List games where the authenticated player is already a participant.

Behavior:
- Requires Basic Auth.
- Uses the Basic Auth username as the player name filter.

### POST /games

Create a new game and immediately join the authenticated player.

Request body:

```json
{
  "num_players": 2
}
```

Behavior:
- Requires Basic Auth.
- Valid `num_players` values are `2`, `3`, or `4`.
- The response contains the creator with a visible rack.
- The game remains `waiting_for_players` until all seats are filled.

### POST /games/{game_id}/players

Join an existing game using the Basic Auth username.

Behavior:
- Requires Basic Auth.
- Request body is ignored by the current implementation.
- If the player already joined, the endpoint returns that player's current curated view.
- When the last open seat is filled, the game automatically transitions to `in_progress`.

### GET /games/{game_id}/players/{player_id}

Return a curated game-state view for the supplied `player_id`.

Behavior:
- Does not currently require auth.
- If `player_id` exists in the game, that player's rack is returned and all others are hidden to counts.
- Returns `403` if the player is not in the game and `404` if the game does not exist.

### POST /games/{game_id}/players/{player_id}/actions/play

Submit a full board end-state for a play action.

Request body:

```json
{
  "melds": [
    {
      "id": "10ka-10ra-10ba",
      "kind": "group",
      "tiles": ["10ka", "10ra", "10ba"]
    }
  ]
}
```

Behavior:
- Does not currently require auth.
- `melds` represents the complete board after the move.
- The engine validates turn ownership, tile ownership for newly played tiles, meld validity, and the initial meld threshold.
- The turn advances automatically on success.

Known limitation:
- The server does not yet fully validate board tile conservation after replacement. See `doc/CODE_REVIEW.md`.

### POST /games/{game_id}/players/{player_id}/actions/draw

Draw one random tile from the pool for the supplied player.

Request body:

```json
{}
```

Behavior:
- Does not currently require auth.
- Draw succeeds only on the player's turn.
- The turn advances automatically on success.

### DELETE /games/{game_id}

Delete a game by ID.

Behavior:
- No authentication is currently required.
- Returns `{ "status": "deleted", "game_id": ... }` on success.

## Error Model

Errors are returned as:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": null
  }
}
```

Current mappings:

- `GAME_NOT_FOUND` -> `404`
- `CONCURRENT_MODIFICATION` -> `503`
- `GAME_NOT_STARTED` -> `400`
- `GAME_COMPLETED` -> `400`
- `PLAYER_NOT_IN_GAME` -> `403`
- `NOT_PLAYER_TURN` -> `403`
- `TILE_NOT_OWNED` -> `422`
- `INVALID_MELD` -> `422`
- `INVALID_BOARD_STATE` -> `422`
- `INSUFFICIENT_INITIAL_MELD` -> `422`
- `POOL_EMPTY` -> `400`
- `INVALID_GAME_STATE` -> `400`
- Unhandled exceptions -> `500`

## Request Models

### CreateGameRequest

```json
{
  "num_players": 2
}
```

### PlayTilesRequest

```json
{
  "melds": [
    {
      "id": "string",
      "kind": "group",
      "tiles": ["7ra", "7ba", "7ka"]
    }
  ]
}
```

### DrawTileRequest

```json
{}
```

## Notes For Client Authors

- Tile IDs are plain strings, not nested tile objects.
- Joined-player arrays can be shorter than `num_players` because unjoined seats are omitted.
- The API does not currently return `current_player_name`; clients must derive it from `players[current_player_index]` when the player list is complete enough.
- Treat `winner_player_id` as best-effort until the engine bug is fixed.
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
