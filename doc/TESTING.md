# Testing Strategy

This repository uses pytest for automated testing and separates tests by layer.

## Naming And Discovery

- Test files use the `*_tests.py` pattern.
- `pytest.ini` configures discovery with:

```ini
[pytest]
addopts = -q
testpaths = tests
python_files = *_tests.py
```

## Current Test Layout

The repository currently has 17 discovered test files.

### Models

- `tests/models/initialization_tests.py`
- `tests/models/model_validation_tests.py`
- `tests/models/updated_model_validation_tests.py`
- `tests/models/integration_tests.py`
- `tests/models/tile_utils_tests.py`
- `tests/models/deterministic_meld_tests.py`
- `tests/models/joker_run_validation_fix_tests.py`
- `tests/models/name_generator_tests.py`

Coverage in this layer focuses on:
- Pool creation
- Tile parsing and formatting
- Meld validation and joker handling
- Deterministic meld IDs
- Game-state integrity helpers

### Engine

- `tests/engine/game_engine_tests.py`
- `tests/engine/game_actions_tests.py`
- `tests/engine/game_rules_tests.py`
- `tests/engine/meld_validation_fix_tests.py`
- `tests/engine/empty_move_validation_tests.py`

Coverage in this layer focuses on:
- Game lifecycle
- Turn rotation
- Draw and play behavior
- Initial meld validation
- Empty-move rejection
- Meld-content validation

### Service

- `tests/service/game_service_tests.py`
- `tests/service/game_simulation_tests.py`

Coverage in this layer focuses on:
- Redis-backed lifecycle operations
- Locking and persistence behavior
- Scenario-style simulations backed by JSON fixtures in `tests/service/test_data/`

### API

- `tests/api/api_endpoints_tests.py`
- `tests/api/game_name_tests.py`

Coverage in this layer focuses on:
- Health and CRUD endpoints
- Auth-dependent endpoints
- Curated player views
- Error mapping
- Generated game names

## Commands

Recommended local commands:

```bash
ruff check .
mypy src/
pytest tests/ -v --cov=src --cov-report=term-missing
```

Useful targeted runs:

```bash
pytest tests/models/model_validation_tests.py -v
pytest tests/engine/empty_move_validation_tests.py -v
pytest tests/api/api_endpoints_tests.py -v
```

## CI

GitHub Actions CI is defined in `.github/workflows/ci.yml`.

Current pipeline behavior:
1. Start Redis as a service container.
2. Set up Python 3.13.
3. Install the package with `pip install -e .[dev]`.
4. Run pytest with coverage.
5. Upload coverage to Codecov.

## Test Data

The service simulation tests use JSON scenario fixtures such as:

- `simple_win_scenario.json`
- `draw_only_scenario.json`
- `three_player_scenario.json`
- `pool_empty_scenario.json`
- `missing_tiles_scenario.json`
- `extra_tiles_scenario.json`

These fixtures are useful for regression testing state transitions and edge cases.

## Current Gaps

The test suite is broad, but there are still important blind spots:

- No regression coverage for unauthorized access to player-scoped routes
- No regression test that board replacement preserves all previously-board tiles
- Winner-state tests still work around the missing `winner_player_id`
- No browser-level UI smoke tests

These gaps are tracked in `doc/CODE_REVIEW.md` and `TODO.md`.
