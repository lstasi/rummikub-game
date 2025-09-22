# GitHub Copilot Instructions – Rummikub Game

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Build the Repository
- Install dependencies: `pip install -e .[dev]` -- takes ~30 seconds
- All quality gates combined take under 1 second total
- Run quality gates: `ruff check . && mypy src/ && pytest tests/ -v --cov=src --cov-report=term-missing`

### Quality Gates (Required Before Any Commit)
- **Lint**: `ruff check .` -- takes ~0.01s, must return "All checks passed!"
- **Type Check**: `mypy src/` -- takes ~0.3s, must return "Success: no issues found"
- **Tests**: `pytest tests/ -v --cov=src --cov-report=term-missing` -- takes ~0.3s, all tests must pass

### Test File Naming Convention
- **Test files use the `*_tests.py` pattern** (e.g., `model_validation_tests.py`, `game_engine_tests.py`)
- Configuration in `pytest.ini` specifies `python_files = *_tests.py`
- Create tests under appropriate subdirectories: `tests/models/`, `tests/engine/`, etc.

### Development Workflow
- **ALWAYS use the pyrun script**: `./scripts/pyrun.sh "python code here"` for testing models
- **Interactive mode**: `./scripts/pyrun.sh -i` for exploration
- **File execution**: `./scripts/pyrun.sh -f path/to/script.py`

### Examples of Working with the Codebase
```bash
# Test basic tile creation
./scripts/pyrun.sh "
from rummikub.models import Color, NumberedTile, TileInstance
tile = TileInstance(kind=NumberedTile(number=7, color=Color.RED))
print(f'Created: {tile} (ID: {tile.id})')
"

# Test meld validation
./scripts/pyrun.sh "
from rummikub.models import Color, NumberedTile, TileInstance, Meld, MeldKind

# Create a valid group (same number, different colors)
tiles = [
    TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
    TileInstance(kind=NumberedTile(number=7, color=Color.BLUE)),
    TileInstance(kind=NumberedTile(number=7, color=Color.BLACK))
]

group = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
tile_instances = {str(t.id): t for t in tiles}
group.validate_with_tiles(tile_instances)
print(f'Valid group with value: {group.get_value(tile_instances)}')
"
```

## Current Capabilities

### What You Can Build and Test
- **Models layer**: Complete implementation with validation, serialization
- **Domain logic**: Tile management, meld validation, game state tracking
- **All basic Rummikub rules**: Groups, runs, jokers, initial meld requirements

### What Is NOT Yet Implemented
- **API layer**: No FastAPI server to run
- **Service layer**: No Redis integration
- **UI layer**: No user interface
- **Docker**: No containerization yet

### Validation Scenarios
Always run these scenarios after making model changes:
1. **Tile Creation**: Create numbered tiles and jokers with valid/invalid parameters
2. **Meld Validation**: Test groups (same number, different colors) and runs (consecutive numbers, same color)
3. **Joker Handling**: Test joker assignment in groups and runs  
4. **Game State**: Create players and game states
5. **Initial Meld**: Test 30-point minimum requirement validation

## Contributing Workflow

### Golden Rules
- Follow the TODO list strictly (`TODO.md`) - work on one task at a time
- Use the 5-step loop: Propose → Update docs → Implement → Test → Quality gates
- Never leave the repo broken - fix or revert within the same task
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, etc.)

### Required Documentation Files
Update these docs BEFORE coding (located in `doc/`):
- `ARCHITECTURE.md` - System overview  
- `MODELS.md` - Domain model design (already comprehensive)
- `ENGINE.md` - Game engine API
- `SERVICE.md` - Redis integration design
- `API.md` - REST endpoints design  
- `UI.md` - User interface flows
- `DEPLOYMENT.md` - Docker and deployment
- `TESTING.md` - Test strategy (already detailed)

### Reference Files
- `RUMMIKUB_RULES.md` - Authoritative game rules
- `TODO.md` - Current active task (follow strictly)

## Technology Constraints

### Stack
- **Language**: Python 3.11+ (3.12 available)
- **Models**: Dataclasses (not Pydantic models despite dependency)
- **API**: FastAPI (not yet implemented)
- **Storage**: Redis (not yet implemented) 
- **Testing**: pytest with 87% coverage
- **Linting**: ruff + mypy

### Key Packages
- Core: `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `redis>=5.0`  
- Testing: `pytest>=8.3`, `pytest-cov>=5.0`, `fakeredis>=2.23`, `httpx>=0.27`
- Quality: `ruff>=0.6`, `mypy>=1.11`

## Common Tasks

### Run the Test Suite
```bash
# Basic test run
pytest

# With coverage report  
pytest --cov=src --cov-report=term-missing

# Specific test file
pytest tests/models/model_validation_tests.py -v
```

### Fix Code Quality Issues
```bash  
# Auto-fix linting issues
ruff check --fix .

# Check type annotations
mypy src/

# Run all quality gates
ruff check . && mypy src/ && pytest tests/ -v
```

### Explore the Models
```bash
# Interactive exploration
./scripts/pyrun.sh -i

# Then in Python:
from rummikub.models import *
help(TileInstance)
help(Meld)
```

## Repository Structure

### Source Code
```
src/rummikub/
├── __init__.py
├── models/
│   ├── __init__.py          # Main exports
│   ├── base.py              # UUID generation utilities
│   ├── tiles.py             # Color, NumberedTile, JokerTile, TileInstance  
│   ├── melds.py             # Meld, MeldKind with validation
│   ├── game.py              # Player, Rack, Pool, Board, GameState
│   ├── actions.py           # Turn, ActionType, Move
│   └── exceptions.py        # Domain-specific exceptions
```

### Tests
```
tests/
├── conftest.py              # pytest fixtures
└── models/
    ├── initialization_tests.py   # Basic model creation
    └── model_validation_tests.py # Validation rules
```

### Documentation
```
doc/
├── ARCHITECTURE.md          # High-level design
├── MODELS.md               # Domain model specs (comprehensive)
├── ENGINE.md               # Game engine design (stub)
├── SERVICE.md              # Redis integration design (stub)
├── API.md                  # REST API design (stub)  
├── UI.md                   # UI flows design (stub)
├── DEPLOYMENT.md           # Docker setup (stub)
└── TESTING.md              # Test strategy (detailed)
```

## Domain Model Reference

### Core Entities
- **Color**: `BLACK`, `RED`, `BLUE`, `ORANGE` 
- **TileInstance**: Physical tile with UUID and kind (NumberedTile or JokerTile)
- **Meld**: GROUP (same number, different colors) or RUN (consecutive numbers, same color)
- **Player**: Has ID, name, rack, and initial_meld_met flag
- **GameState**: Contains players, pool, board, and game status

### Validation Rules
- **Groups**: 3-4 tiles, same number, all different colors
- **Runs**: 3+ tiles, consecutive numbers, same color, no wrapping (12-13-1 invalid)
- **Initial Meld**: Must total ≥30 points before first board play
- **Jokers**: Take value of tile they represent, can be retrieved by replacement

### Key Methods
```python  
# Tile validation
meld.validate_with_tiles(tile_instances)  # Raises InvalidMeldError
meld.get_value(tile_instances)           # Returns point value

# Game setup
pool, tiles = Pool.create_full_pool()    # 106 tiles per Rummikub rules
player = Player(id=str(uuid4()), name="Alice")
```

## Troubleshooting

### Import Errors
- Ensure you've run `pip install -e .[dev]`
- Use `./scripts/pyrun.sh` instead of direct python commands
- Check that you're in the repository root directory

### Test Failures
- Run tests individually: `pytest tests/models/model_validation_tests.py::TestClass::test_method -v`
- Use `./scripts/pyrun.sh` to reproduce test scenarios interactively

### Linting/Type Errors
- Run `ruff check --fix .` for auto-fixes
- For mypy errors, ensure proper type annotations and imports
- All type annotations use forward references (`"ClassName"`) due to circular imports

## Notes

- This repository follows incremental development: only the models layer is complete
- No API server can be started yet - just model validation and testing  
- Docker/Redis integration comes in later TODO items
- Always validate changes with the pyrun script before committing
- Coverage goal is 90%+ for implemented layers