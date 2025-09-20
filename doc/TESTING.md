# Testing Strategy

Pytest structure, fixtures, coverage expectations, and CI checks.

## Current Test Suite

The project uses pytest for testing with the following structure:
- `tests/models/` - Unit tests for domain models (tiles, melds, game state)
- `conftest.py` - Global pytest configuration and fixtures

## Test Execution

### Local Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/models/test_model_validation.py -v
```

### Continuous Integration

The project uses GitHub Actions for automated testing:
- **Triggers**: Push to main branch, pull requests to main
- **Python versions**: 3.11, 3.12
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
- Engine tests (`tests/engine/`)
- Service tests (`tests/service/`) 
- API tests (`tests/api/`)
