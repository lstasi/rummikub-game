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
- `conftest.py` - Global pytest configuration and fixtures

Current test files:
- `tests/models/initialization_tests.py` - Basic model creation and setup
- `tests/models/model_validation_tests.py` - Validation rules and edge cases

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

As of the latest run: 88% coverage (367 statements, 45 missed)

## Future Test Additions

To be updated as tests are introduced for each layer:
- Engine tests (`tests/engine/`) - Using `*_tests.py` naming pattern
- Service tests (`tests/service/`) - Using `*_tests.py` naming pattern
- API tests (`tests/api/`) - Using `*_tests.py` naming pattern
