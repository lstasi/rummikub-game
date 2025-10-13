# Project TODOs

This list includes only pending tasks. Completed items are tracked in the repository history and README.

- [x] Implement models package
  - Create `src/rummikub/models/` with Pydantic models or dataclasses implementing: Color, Tile, Joker, Meld (Group/Run), Rack, Pool, Board, Player, GameState, Turn, Move. Include validation and serialization helpers.
- [x] Unit tests for models
  - Add tests under `tests/models/` covering valid/invalid groups/runs, joker handling, initial meld scoring, and serialization round-trips.
- [x] Define game engine
  - Update `doc/ENGINE.md` with responsibilities, API contracts (setup, turn flow, play/rearrange validation, joker retrieval, scoring, end-of-game) and error taxonomy.
- [x] Implement game engine
  - Create `src/rummikub/engine/` implementing the defined API. Keep logic minimal to pass tests.
- [x] Unit tests for engine
  - Add tests under `tests/engine/` for legal/illegal plays, rearrangement validity, joker replacement, initial meld, win state.
- [x] Define game service
  - Update `doc/SERVICE.md` with Redis schema (keys/data structures), concurrency model (locking/optimistic), and service API.
- [x] Implement game service
  - Create `src/rummikub/service/` with Redis integration; DI-friendly to use `fakeredis` in tests.
- [x] Unit tests for service
  - Add tests under `tests/service/` covering lifecycle, state transitions, concurrency edges, and error handling.
- [x] Define API interface
  - Update `doc/API.md` with REST/WebSocket endpoints, request/response contracts, and error model.
- [x] Implement API interface
  - Create `src/rummikub/api/` using FastAPI. Wire endpoints to service. Include OpenAPI and validation.
- [x] Unit tests for API
  - Add tests under `tests/api/` using FastAPI TestClient for success and failure paths.
- [x] Dockerize and compose
  - Add Dockerfile and docker-compose.yml (API + Redis). Update `doc/DEPLOYMENT.md` with run instructions.
- [x] UI definition
  - Update `doc/UI.md` with minimal UI flows and API usage.
- [ ] Implement UI (MVP)
  - Create basic UI that consumes the API.
  
### UI Implementation Phases

#### Phase 1: Simple Button-Based UI (MVP)
- Basic game screens (home, game list, create/join, lobby)
- Simple game board and player rack display
- Button-based interactions (no drag-and-drop):
  - "Push to Board" - move selected tiles from rack to create new meld
  - "Remove from Board" - move tiles from board back to rack
  - "Break Meld" - split existing meld on board into individual tiles
  - "Group Meld" - combine selected tiles on board into new meld
- Tile selection via click/tap
- Turn management (play tiles, draw tile)
- Basic validation and error messages

#### Phase 2: Enhanced Interactions
- Drag-and-drop tile placement
- Visual meld building helpers
- Improved tile arrangement and sorting
- Better error feedback and validation
- Mobile touch optimizations

#### Phase 3: Advanced Features
- Real-time updates via WebSocket
- Advanced accessibility features
- Animations and visual polish
- Game statistics and history

### Authentication Implementation (MVP)

#### Current State
- Username is passed in request body (`player_name` field)
- No authentication mechanism
- Game list shows all games
- Frontend has username input fields on create/join pages

#### Target State
- Username extracted from HTTP Basic Auth header
- API returns 401 when no auth header present
- Username removed from API request bodies
- Password validation delegated to upper layer (load balancer/API gateway)
- Game list filtered to show only user's games
- Separate endpoint lists games user can join (status=waiting_for_players)
- Frontend sends username via Basic Auth header
- Username input fields removed from UI

#### Implementation Steps
1. **Backend - Auth Dependency**
   - Create `get_current_username()` dependency in `dependencies.py`
   - Extract username from `Authorization: Basic` header
   - Decode base64 credentials (format: "username:password")
   - Return username (ignore password as validation happens upstream)
   - Raise 401 HTTPException if no auth header or invalid format

2. **Backend - API Updates**
   - Remove `player_name` from `CreateGameRequest` model
   - Remove `player_name` from `JoinGameRequest` model
   - Add `CurrentUserDep` (username dependency) to:
     - `POST /games` - use for first player joining
     - `POST /games/{game_id}/players` - use for joining player
   - Update `GET /games` to accept optional `username` parameter
     - Filter to show only games where user is a player
     - Default behavior: show all games (backward compatible)
   - Add new endpoint `GET /games/available` 
     - Returns games with status=waiting_for_players (user can join these)
   - Update `GET /games/{game_id}/players/{player_id}` to validate auth
     - Ensure authenticated username matches the player_id's name

3. **Frontend - Auth Header**
   - Update `API.request()` in `main.js` to add Basic Auth header
   - Prompt for username on first visit (store in localStorage)
   - Format: `Authorization: Basic base64(username:dummy_password)`
   - Use empty or dummy password (validation happens upstream)

4. **Frontend - UI Updates**
   - Remove player name input from `create.html`
   - Remove player name input from `join.html`
   - Update `create.js` - remove playerName collection, use auth
   - Update `join.js` - remove playerName collection, use auth
   - Update `home.js`:
     - Change player links to display only (no click action)
     - Add "Join" button on each game card (for waiting_for_players status)
     - Filter games to show user's games (use username query param)
     - Show separate section for "Available Games" (games user can join)

5. **Testing**
   - Add auth tests in `tests/api/`
   - Test 401 response when no auth header
   - Test username extraction from various auth header formats
   - Test game list filtering by username
   - Update existing API tests to include auth header

6. **Documentation**
   - Update `doc/API.md` with authentication section
   - Document Basic Auth header requirement
   - Document new/updated endpoints
