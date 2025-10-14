# Testing Strategy

Pytest structure, fixtures, coverage expectations, and CI checks.

## Test File Naming Convention

The project uses the `*_tests.py` naming pattern for all test files:
- Test files end with `_tests.py` (e.g., `model_validation_tests.py`, `game_engine_tests.py`)
- Configuration in `pytest.ini` specifies `python_files = *_tests.py`
- Tests are organized in subdirectories matching the source structure

## Current Test Suite

The project uses pytest for testing with the following structure:
- `tests/models/` - Unit tests for domain models (tiles, melds, game state)
- `tests/engine/` - Unit tests for game engine (actions, rules, game logic)
- `tests/service/` - Unit tests for service layer (game service, Redis integration)
- `tests/api/` - Integration and unit tests for API endpoints
- `conftest.py` - Global pytest configuration and fixtures

Current test files:
- `tests/models/initialization_tests.py` - Basic model creation and setup
- `tests/models/model_validation_tests.py` - Validation rules and edge cases
- `tests/models/updated_model_validation_tests.py` - Additional validation tests
- `tests/models/integration_tests.py` - Integration tests for models
- `tests/models/tile_utils_tests.py` - Tile utility function tests
- `tests/models/deterministic_meld_tests.py` - Deterministic meld ID tests
- `tests/engine/game_engine_tests.py` - Game engine core functionality
- `tests/engine/game_actions_tests.py` - Game action execution tests
- `tests/engine/game_rules_tests.py` - Game rule validation tests
- `tests/service/game_service_tests.py` - Service layer tests (Redis integration)
- `tests/service/game_simulation_tests.py` - End-to-end game simulation tests
- `tests/api/api_endpoints_tests.py` - API endpoint tests (integration and mocked)

## Test Execution

### Local Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/models/model_validation_tests.py -v
```

### Continuous Integration

The project uses GitHub Actions for automated testing:
- **Triggers**: Push to main branch, pull requests to main
- **Python version**: 3.13
- **Test coverage**: Collected and can be uploaded to Codecov
- **Workflow**: `.github/workflows/ci.yml`

The CI pipeline:
1. Sets up Python environment
2. Installs project dependencies (`pip install -e .[dev]`)  
3. Runs pytest with coverage reporting
4. (Optional) Uploads coverage to Codecov

## Current Coverage

As of the latest run: 89% coverage (1130 statements, 125 missed)

### API Tests

API tests include:
- **Integration tests** (`TestAPIEndpointsIntegration`): Test endpoints with real Redis and GameService
- **Mocked tests** (`TestAPIEndpointsMocked`): Test endpoints with mocked services for fast execution
- **Error handling tests** (`TestAPIErrorHandling`): Test error mapping and exception handling
- **New endpoint tests** (`TestNewAPIEndpoints`): Test authentication, my-games endpoint, auto-join, and status filtering

**Note:** Integration tests require Redis to be running. Use mocked tests for quick validation.
