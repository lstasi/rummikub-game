# Project TODO

This file tracks remaining work only. Core models, engine, service, API, Docker setup, and the button-driven web UI are already implemented.

## Critical Bug Fixes

- [ ] Bind player-scoped routes to authenticated callers
  - Require authentication for `GET /games/{game_id}/players/{player_id}` and both action routes.
  - Reject requests where the authenticated player does not match the target `player_id`.
  - Decide whether `DELETE /games/{game_id}` should stay public or require ownership/admin authorization.
  - Add regression tests for rack privacy, impersonation attempts, and unauthorized moves.

- [ ] Preserve full tile partition during play actions
  - Validate that the submitted board contains every tile previously on the board unless it is legitimately moved or returned under explicit rules.
  - Reject board end-states that silently drop tiles or duplicate tiles.
  - Run `GameState.validate_tile_ownership()` or equivalent post-move partition validation before persisting.
  - Add regression tests for dropped board tiles and duplicated board tiles.

- [ ] Persist winner identity on game completion
  - Set `winner_player_id` in both win paths used by the engine.
  - Add regression tests for engine, service, API, and UI winner display.

## Product And UX Backlog

- [ ] Align the home page turn display with the API contract
  - Either add `current_player_name` to API responses or derive it client-side.
  - Remove dead UI expectations if the field stays server-free.

- [ ] Finish the redesigned home-page UX
  - Populate the authenticated player banner.
  - Complete translation coverage for the redesigned home page and rules dialog.
  - Replace the blocking `alert()` rules dialog with an in-page modal.

- [ ] Decide on completed-game UX
  - Route to the dedicated win page when games end, or remove the unused page if in-game completion is the intended flow.

- [ ] Replace polling with push-based updates
  - Move home-page and game-page refresh from polling to WebSocket or SSE.

- [ ] Add drag-and-drop gameplay interactions
  - Keep the current button-driven flow as the fallback interaction model.

## Reliability And Operations

- [ ] Harden Redis locking for higher contention
  - Replace the current fixed 5-second spin lock with a safer renewable or Lua-backed approach.

- [ ] Add UI smoke tests
  - Cover the home page, join flow, draw/play flow, and completed-game flow.

- [ ] Add deployment smoke checks
  - Verify the combined app serves `/`, `/docs`, and `/api/v1/health` in CI or release pipelines.

## Nice-To-Have Features

- [ ] Game history and move audit trail
- [ ] Better action error explanations in the UI
- [ ] Accessibility improvements beyond current button-label translation support
- [ ] Stronger session/authentication model than Basic Auth username-only identity
