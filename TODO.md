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
- [ ] Define API interface
  - Update `doc/API.md` with REST/WebSocket endpoints, request/response contracts, and error model.
- [ ] Implement API interface
  - Create `src/rummikub/api/` using FastAPI. Wire endpoints to service. Include OpenAPI and validation.
- [ ] Unit tests for API
  - Add tests under `tests/api/` using FastAPI TestClient for success and failure paths.
- [ ] Dockerize and compose
  - Add Dockerfile and docker-compose.yml (API + Redis). Update `doc/DEPLOYMENT.md` with run instructions.
- [ ] UI definition
  - Update `doc/UI.md` with minimal UI flows and API usage.
- [ ] Implement UI (MVP)
  - Create basic UI that consumes the API.
