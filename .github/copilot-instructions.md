# GitHub Copilot Working Instructions – Rummikub Game

These instructions define how any agent (or human) must work on this repository. The core rule: only perform the exact step currently marked active in the project TODO list. Do not jump ahead.

Reference rules: see `RUMMIKUB_RULES.md`.

## Golden Rules

- Follow the ordered TODO list strictly. Work on one task at a time.
- For every task, use this 5-step loop:
  1) Propose changes
  2) Update documentation
  3) Implement minimal code
  4) Add/Update tests
  5) Run quality gates and summarize
- Keep changes narrowly scoped to the current task. Defer anything extra as a follow-up TODO.
- Prefer small, frequent commits following Conventional Commits.
- Never leave the repo in a broken state. If something fails, fix or revert within the same task.

## Repository structure (planned)

Do not create files outside the current task. Future tasks will introduce the following structure:

- `src/` – Application code (Python package: `rummikub`)
- `tests/` – Pytest test suite
- `doc/` – Architecture and component docs (longform)
- Docker/Compose files for containerized runs

## Technology constraints

- Language: Python (>=3.11 recommended)
- Storage: Redis (backend state)
- Testing: pytest
- API: FastAPI (assumption unless specified otherwise)
- Containers: Docker + docker-compose

## Required documentation set (to be created by later tasks)

Do not create these files until their corresponding TODO is active. When working on a task, update or create the relevant doc below:

- `doc/ARCHITECTURE.md` – high-level system overview, component diagram, data flow
- `doc/MODELS.md` – domain model design, invariants, serialization
- `doc/ENGINE.md` – game engine responsibilities, public API, algorithms
- `doc/SERVICE.md` – service layer with Redis integration, keys, locking/transactions
- `doc/API.md` – REST endpoints (and/or WebSocket), request/response contracts
- `doc/UI.md` – UI flows, components, API usage
- `doc/DEPLOYMENT.md` – Dockerfile, docker-compose, environment vars, runbook
- `doc/TESTING.md` – test strategy, fixtures, coverage goals, CI checks

For classes and functions, include clear docstrings (Google or NumPy style) and type hints.

## Step workflow template (apply to every TODO)

For the current TODO, follow this exact sequence:

1) Propose changes
- Summarize the intent and scope.
- List files to add/change (paths) and the nature of each change.
- Define public interfaces (function/class signatures, endpoints, data shapes) and error modes.
- Identify edge cases and assumptions.
- Acceptance criteria checklist (see template below).

2) Update documentation
- Update the relevant `doc/*.md` file(s) for the task BEFORE coding.
- Add diagrams or tables as needed (keep text authoritative and concise).
- Cross-link to `RUMMIKUB_RULES.md` where rules inform behavior.

3) Implement minimal code
- Add code strictly matching the documented interfaces.
- Keep implementation minimal for the acceptance criteria. Avoid speculative features.
- Include docstrings and type annotations.

4) Add/Update tests (pytest)
- Write tests that enforce the acceptance criteria.
- Cover happy path and at least 1–2 edge cases per public API.
- Prefer fast, isolated unit tests. Use `fakeredis` for service layer tests.

5) Run quality gates and summarize
- Lint/format (e.g., ruff/black if configured), type check (mypy if configured), run `pytest`.
- Provide a short PASS/FAIL summary and fix failures.
- If new external dependencies were added, ensure they are pinned and documented.

If any part cannot be completed within the current task scope, add a new TODO with a concise description.

## Acceptance criteria template

For each task, define and meet criteria like the following:

- Documentation: Relevant `doc/*.md` updated with design and API/contracts.
- Code: Public API implemented with docstrings and types; no dead code.
- Tests: Pytest cases added; cover success + 1–2 edge cases; deterministic.
- Quality gates: Lint/typecheck/test all PASS locally.
- Build/run: If applicable, local run instructions updated under the relevant doc.

## Commit and PR guidelines

- Use Conventional Commits:
  - feat: new feature
  - fix: bug fix
  - docs: documentation only changes
  - test: adding or updating tests
  - chore/build/ci/refactor/perf/style as appropriate
- Keep commits scoped to the task; avoid mixing concerns.
- PR Checklist:
  - [ ] Proposed changes section present
  - [ ] Docs updated first
  - [ ] Code matches docs
  - [ ] Tests added/updated and passing
  - [ ] Quality gates PASS summary
  - [ ] No TODOs left untracked

## Game domain coverage expectations

Use `RUMMIKUB_RULES.md` as the authoritative source for rules. The implementation must support:
- Tiles: numbers 1–13 in four colors, 2 sets each; 2 jokers
- Valid combinations: groups (same number, distinct colors), runs (consecutive numbers, same color)
- Initial meld total value >= 30
- Turn actions: play tiles or draw one tile
- Board rearrangement: always end turn with all melds valid
- Joker rules: substitution, value based on position, retrieval via replacement
- Winning and optional scoring (per rules)

Edge cases to cover in design and tests:
- Duplicate colors in a group (invalid)
- Runs crossing 1 or 13 boundaries or mixing colors (invalid)
- Joker retrieval and reuse in the same turn
- Initial meld valuation with jokers
- Rearrangement that temporarily invalidates but finishes valid
- Empty pool draws; end-of-game conditions

## Area-specific instructions

### Models (definitions then implementation)
- Propose: Data types for Tile, Joker, Color, Group, Run, Meld, Rack, Pool, Board, Player, GameState, Turn, Move.
- Docs: `doc/MODELS.md` with invariants, validation, and serialization (JSON) rules.
- Code: `src/rummikub/models/*` with dataclasses or Pydantic models; validation methods; serde helpers.
- Tests: `tests/models/*` for validation, scoring utilities (initial meld), joker handling, serialization round-trip.

### Game Engine (definition then implementation)
- Propose: Engine responsibilities and API (setup, turn flow, play/rearrange, scoring, end-of-game); error taxonomy.
- Docs: `doc/ENGINE.md` with method contracts, inputs/outputs, state transitions.
- Code: `src/rummikub/engine/*` implementing the contracts; keep rearrangement logic incremental but valid.
- Tests: `tests/engine/*` covering legal/illegal plays, rearrangement validity, initial meld, joker retrieval, win state.

### Game Service (definition then implementation)
- Propose: Redis schema (keys, data structures), optimistic locking or Lua scripts, session/invite flows.
- Docs: `doc/SERVICE.md` with API, concurrency model, failure handling.
- Code: `src/rummikub/service/*` with Redis adapter interface + implementation; DI-friendly for tests.
- Tests: `tests/service/*` using `fakeredis`; cover lifecycle, concurrency edges, error paths.

### API Interface (definition then implementation)
- Propose: REST endpoints (or WebSocket events), JSON contracts, auth/session (invite code), error model.
- Docs: `doc/API.md` with OpenAPI excerpts and payload examples.
- Code: `src/rummikub/api/*` using FastAPI; schemas with Pydantic; error handling unified.
- Tests: `tests/api/*` using FastAPI TestClient; cover success and failure paths.

### UI (definition then implementation)
- Propose: Minimal UI flows to create/join game, view rack/board, play/rearrange.
- Docs: `doc/UI.md` with component/flow diagrams, API calls.
- Code: Place under a future `ui/` (or integrate a simple static client) as defined by the UI task.
- Tests: Add minimal UI tests if framework supports; otherwise document manual smoke steps.

### Dockerization and Compose
- Propose: Container boundaries, environment variables, volumes, ports.
- Docs: `doc/DEPLOYMENT.md` with full run instructions and troubleshooting.
- Code: `Dockerfile`, `docker-compose.yml`; healthchecks; dev vs prod notes.
- Tests: Smoke test in CI (build + start + ping health endpoint) where feasible.

## Quality gates checklist (run each task)

- Build/package config valid (pyproject/requirements as applicable)
- Lint: no errors (ruff/flake8) – optional until configured
- Types: mypy – optional until configured
- Tests: `pytest` PASS locally
- Containers: if touched, build succeeds and services start locally

## Proposal template (copy into task description)

- Summary: <what and why>
- Files: <add/edit paths>
- Public API: <signatures/contracts>
- Edge cases: <list>
- Assumptions: <list>
- Acceptance criteria: <list of verifiable checks>

## Notes

- If a rule here conflicts with the TODO’s explicit instructions, the TODO wins.
- When in doubt, keep changes small and well-documented, and add a TODO for follow-ups.
