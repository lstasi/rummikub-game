# Architecture

This document describes the architecture that is currently implemented in the repository.

## Runtime Topology

The application runs as a combined FastAPI server in `main.py`.

- The root app serves the static browser UI from `static/`.
- The API app is mounted under `/api/v1` from `src/rummikub/api/main.py`.
- Redis stores persisted game state and per-game lock keys.

High-level flow:

`Browser UI -> FastAPI API -> GameService -> GameEngine -> Domain Models -> Redis`

## Layers

### Models

`src/rummikub/models/` contains the domain objects used across the stack.

- Tiles are represented as deterministic strings such as `7ra` or `ja`.
- Melds are dataclasses with built-in validation and deterministic IDs.
- Game state is a dataclass composed of players, pool, board, status, and timestamps.

### Engine

`src/rummikub/engine/` enforces gameplay rules.

- `game_engine.py` exposes the public orchestration API.
- `game_actions.py` applies joins, plays, draws, and turn advancement.
- `game_rules.py` performs validation such as turn checks, meld validation, and initial meld scoring.

The engine is intentionally stateless. Every operation accepts a `GameState` and returns a new `GameState`.

### Service

`src/rummikub/service/game_service.py` adds persistence and basic concurrency control.

- Games are serialized to Redis JSON blobs.
- A simple per-game lock key protects read-modify-write updates.
- The service returns curated game views that hide other players' rack contents.

### API

`src/rummikub/api/` exposes the HTTP contract.

- Pydantic models define request and response schemas.
- Dependency functions create Redis clients, services, and Basic Auth identity.
- Exception handlers map domain and service errors to structured JSON responses.

### UI

The UI is a static HTML/CSS/JavaScript client.

- `home.html` shows quick-create, my games, and available games.
- `game.html` supports button-driven tile manipulation and polling-based refresh.
- `win.html` exists as a separate results page, although the current in-game flow primarily shows completion inline.

## Data Model Highlights

### Tile Identity

The repository does not use runtime tile wrapper objects. Physical tiles are represented directly by tile ID strings.

- Numbered tile: `{number}{color_code}{copy}`
- Joker tile: `j{copy}`

This keeps storage compact and simplifies serialization, debugging, and tests.

### Game Initialization

`GameState.create_initialized_game()` creates the full pool and pre-deals 14-tile racks for every player slot before anyone joins.

Effects of this design:
- Pool size immediately reflects the final number of seats.
- Joining a game attaches a name to a pre-created player slot.
- Auto-start happens when every seat has been joined.

## Request And State Flow

### Create And Join

1. API receives `POST /games` with Basic Auth.
2. Service creates a game via the engine and persists it.
3. Service immediately joins the authenticated player.
4. API returns a curated state where only the creator sees a rack.

### Play Or Draw

1. API loads the game through the service.
2. Service acquires the per-game Redis lock.
3. Engine validates the action and returns an updated `GameState`.
4. Service persists the new state and returns a curated response.

### Polling

The current UI polls:
- Home page every 5 seconds
- Game page every 3 seconds

There is no WebSocket or SSE transport yet.

## Operational Constraints

- Redis locking is simple and suitable for low contention, not high-scale concurrency.
- Authentication is inconsistent across endpoints. See `doc/CODE_REVIEW.md`.
- Board replacement currently depends on the caller submitting a valid end-state. A stronger tile-partition validation pass is still needed.

## Related Documents

- `doc/MODELS.md`
- `doc/ENGINE.md`
- `doc/SERVICE.md`
- `doc/API.md`
- `doc/UI.md`
- `doc/CODE_REVIEW.md`
