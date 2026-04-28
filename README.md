# Rummikub Game

Rummikub Game is a Python implementation of the game with a dataclass-based domain model, a rule-enforcing engine, a Redis-backed service layer, a FastAPI API, and a static browser UI.

## Current Status

[![CI](https://github.com/lstasi/rummikub-game/workflows/CI/badge.svg)](https://github.com/lstasi/rummikub-game/actions/workflows/ci.yml)
[![Docker](https://github.com/lstasi/rummikub-game/workflows/Docker/badge.svg)](https://github.com/lstasi/rummikub-game/actions/workflows/docker.yml)

The repository already includes:
- Deterministic tile IDs and full pool/rack/board/game-state models
- Game-engine validation for turns, melds, initial melds, draws, and wins
- Redis persistence with per-game locking
- FastAPI endpoints for game discovery, join flow, game state, play, draw, delete, and health
- Static HTML/CSS/JavaScript pages for home, game, and win flows
- Docker packaging and GitHub Actions workflows

Open defects and review findings are tracked in `doc/CODE_REVIEW.md`.
Remaining work is tracked in `TODO.md`.

## Quick Start

### Local Development

```bash
pip install -e .[dev]
docker compose up redis -d
python main.py --reload
```

Application URLs:
- UI: `http://localhost:8090/`
- API root: `http://localhost:8090/api/v1`
- OpenAPI docs: `http://localhost:8090/docs`
- Health check: `http://localhost:8090/api/v1/health`

### Docker Compose

```bash
docker compose up -d
docker compose logs -f rummikub
```

This starts:
- `rummikub` on port `8090`
- `redis` on port `6379`

## Authentication Model

The current UI and API use HTTP Basic Auth for discovery and join flows.

- Username: player name
- Password: accepted but not validated

Protected endpoints today:
- `GET /api/v1/games`
- `GET /api/v1/games/my-games`
- `POST /api/v1/games`
- `POST /api/v1/games/{game_id}/players`

Player-scoped state and action routes currently rely on `player_id` in the path instead of binding the caller identity. That is a known security defect documented in `doc/CODE_REVIEW.md`.

## Project Structure

- `src/rummikub/models/`: tiles, melds, game state, actions, exceptions, name generation
- `src/rummikub/engine/`: gameplay rules and turn execution
- `src/rummikub/service/`: Redis-backed persistence and locking
- `src/rummikub/api/`: FastAPI routes, API models, dependencies, exception mapping
- `static/`: HTML, CSS, and JavaScript UI assets
- `tests/`: pytest suites for models, engine, service, and API
- `doc/`: architecture, contracts, deployment, testing, review notes

## Development Commands

Quality gates used by the repository:

```bash
ruff check .
mypy src/
pytest tests/ -v --cov=src --cov-report=term-missing
```

Useful local commands:

```bash
./scripts/pyrun.sh -i
./scripts/pyrun.sh -f path/to/script.py
./scripts/pyrun.sh "from rummikub.models import TileUtils; print(TileUtils.create_full_tile_set()[:5])"
```

## Documentation Map

- `doc/ARCHITECTURE.md`: current system layout and runtime data flow
- `doc/MODELS.md`: domain model and tile ID format
- `doc/ENGINE.md`: engine responsibilities and move flow
- `doc/SERVICE.md`: Redis persistence and locking behavior
- `doc/API.md`: REST contract and error model
- `doc/UI.md`: shipped UI flows and current front-end limitations
- `doc/DEPLOYMENT.md`: Docker, local run, and CI/CD usage
- `doc/TESTING.md`: test suite layout and quality gates
- `doc/CODE_REVIEW.md`: prioritized bug list and review findings

## Notes

- Python package metadata requires Python `>=3.11`.
- CI and the Docker image use Python `3.13`.
- The UI supports English, Portuguese, and Spanish button labels through `static/js/i18n.js`, but translation coverage is not complete yet.
