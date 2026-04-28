# GitHub Copilot Instructions – Rummikub Game

Always reference these instructions first and fallback to search or bash commands only when the repository does not match the information below.

## Working Effectively

### Bootstrap and Build the Repository
- Install dependencies: `pip install -e .[dev]`
- Run quality gates: `ruff check . && mypy src/ && pytest tests/ -v --cov=src --cov-report=term-missing`
- Use `./scripts/pyrun.sh` for quick model and rule exploration

### Quality Gates
- **Lint**: `ruff check .`
- **Type Check**: `mypy src/`
- **Tests**: `pytest tests/ -v --cov=src --cov-report=term-missing`

### Test File Naming Convention
- Test files use the `*_tests.py` pattern
- `pytest.ini` sets `python_files = *_tests.py`
- Organize tests by layer: `tests/models/`, `tests/engine/`, `tests/service/`, `tests/api/`

### Development Workflow
- Update the relevant docs before changing behavior
- Keep changes narrow and validated
- Use Conventional Commit prefixes when writing commit messages
- Add new work to `TODO.md` if it is out of scope for the current task

## Examples of Working with the Codebase

```bash
# Test basic tile creation
./scripts/pyrun.sh "
from rummikub.models import Color, TileUtils
tile_id = TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
print(tile_id, TileUtils.format_tile(tile_id))
"

# Test meld validation
./scripts/pyrun.sh "
from rummikub.models import Color, TileUtils, Meld, MeldKind
tiles = [
    TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
    TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
    TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a'),
]
meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
meld.validate()
print(meld.id, meld.get_value())
"
```

## Current Capabilities

### Implemented Today
- Dataclass-based domain models with deterministic tile IDs
- Game engine for joins, draws, plays, meld validation, initial melds, and win checks
- Redis-backed service with per-game locking
- FastAPI API with request/response models and structured exception handling
- Static browser UI for home, game, and win flows
- Dockerfile, Docker Compose files, CI workflow, and image-publish workflow

### Important Known Gaps
- Player-scoped API routes are not yet bound to the authenticated caller
- Play validation does not yet fully enforce board-tile conservation after board replacement
- `winner_player_id` is not populated consistently on game completion
- UI still uses polling and button-driven board editing instead of push updates and drag-and-drop

Check `doc/CODE_REVIEW.md` and `TODO.md` before starting work.

## Required Documentation Files

Update these docs when behavior changes:
- `doc/ARCHITECTURE.md`
- `doc/MODELS.md`
- `doc/ENGINE.md`
- `doc/SERVICE.md`
- `doc/API.md`
- `doc/UI.md`
- `doc/DEPLOYMENT.md`
- `doc/TESTING.md`
- `doc/CODE_REVIEW.md` when fixing or discovering important bugs

Reference files:
- `RUMMIKUB_RULES.md`
- `TODO.md`

## Technology Constraints

### Stack
- **Language**: Python 3.11+
- **Models**: Dataclasses
- **API**: FastAPI
- **Storage**: Redis
- **Testing**: pytest
- **Linting/Types**: ruff + mypy

### Key Packages
- Core: `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `redis>=5.0`
- Testing: `pytest>=8.3`, `pytest-cov>=5.0`, `fakeredis>=2.23`, `httpx>=0.27`
- Quality: `ruff>=0.6`, `mypy>=1.11`

## Common Tasks

### Run the Test Suite
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Explore the Models
```bash
./scripts/pyrun.sh -i
```

In the interactive shell:

```python
from rummikub.models import *
help(TileUtils)
help(Meld)
```

## Repository Structure

### Source Code
```text
src/rummikub/
├── api/
├── engine/
├── models/
└── service/
```

### Tests
```text
tests/
├── api/
├── engine/
├── models/
└── service/
```

### Documentation
```text
doc/
├── ARCHITECTURE.md
├── API.md
├── BUGFIX_UI_REFRESH.md
├── CODE_REVIEW.md
├── DEPLOYMENT.md
├── ENGINE.md
├── HOME_PAGE_REDESIGN.md
├── MODELS.md
├── SERVICE.md
├── TESTING.md
└── UI.md
```

## Domain Model Reference

### Core Entities
- **Color**: `BLACK`, `RED`, `BLUE`, `ORANGE`
- **Tile IDs**: physical tiles represented as strings like `7ra` or `ja`
- **Meld**: `GROUP` or `RUN`
- **Player**: id, name, rack, joined flag, and initial meld status
- **GameState**: players, pool, board, status, timestamps, and game name

### Validation Rules
- **Groups**: 3-4 tiles, same number, different colors
- **Runs**: 3+ consecutive numbers, same color, no wraparound
- **Initial Meld**: must total at least 30 points
- **Jokers**: resolved contextually inside a meld

### Key Methods
```python
meld.validate()
meld.get_value()

pool = Pool.create_full_pool()
game = GameState.create_initialized_game(2)
```

## Troubleshooting

### Import Errors
- Ensure the package is installed with dev dependencies
- Prefer `./scripts/pyrun.sh` for quick exploration
- Confirm you are running from the repository root

### Test Failures
- Run the narrowest failing test file first
- Use scenario fixtures in `tests/service/test_data/` to reproduce service behavior

### Linting and Type Errors
- Run `ruff check --fix .` for auto-fixable lint issues
- Run `mypy src/` for type errors

## Notes

- The repository is no longer models-only; API, service, UI, and Docker support are already present
- The main executable entry point is `main.py`
- Coverage should continue moving toward 90%+ for implemented layers