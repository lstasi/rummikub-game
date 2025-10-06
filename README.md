# Rummikub Game

Python-based Rummikub game with Redis backend, FastAPI API, and pytest tests. Designed for containerized runs via Docker Compose.

## Status

[![CI](https://github.com/lstasi/rummikub-game/workflows/CI/badge.svg)](https://github.com/lstasi/rummikub-game/actions/workflows/ci.yml)
[![Docker](https://github.com/lstasi/rummikub-game/workflows/Docker/badge.svg)](https://github.com/lstasi/rummikub-game/actions/workflows/docker.yml)

Completed:
- Copilot instructions with strict workflow (`COPILOT_INSTRUCTIONS.md`)
- Base project scaffolding (`src/`, `tests/`, `doc/`, `pyproject.toml`, `pytest.ini`)
- Domain model definitions documented (`doc/MODELS.md`)
- Models package implementation (`src/rummikub/models/`) with full Pydantic validation

Pending (see `TODO.md` for the full list):
- Unit tests for models
- Define and implement engine + tests
- Define and implement service (Redis) + tests
- Define and implement API (FastAPI) + tests
- Dockerfile + docker-compose
- UI definition and MVP

## Repo Structure

- `src/` — Python package code (to be implemented incrementally)
- `tests/` — Pytest suites
- `doc/` — Design docs (architecture, models, engine, service, API, UI, deployment, testing)
- `COPILOT_INSTRUCTIONS.md` — How to work on this repo step-by-step
- `RUMMIKUB_RULES.md` — Game rules reference
- `TODO.md` — Pending tasks with checkboxes

## Technology

- Python >= 3.13, Pydantic, FastAPI, Redis
- pytest for testing
- Docker + docker-compose for local runs
- GitHub Actions for CI/CD

## Features

### Multi-Language Support
The UI supports three languages:
- **English (en)** - Default language
- **Portuguese (pt)** - Brazilian Portuguese
- **Spanish (es)** - Spanish

To use a specific language, add the `lang` query parameter to the URL:
- English: `http://localhost:8000/?lang=en` (or just `http://localhost:8000/`)
- Portuguese: `http://localhost:8000/?lang=pt`
- Spanish: `http://localhost:8000/?lang=es`

The language parameter is automatically preserved when navigating between pages.

## Development

### Running Tests Locally
```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```

### Continuous Integration
The project automatically runs tests on:
- Push to main branch
- Pull requests to main branch  
- Python version: 3.13

See `.github/workflows/ci.yml` for the complete CI configuration.

### Docker Image Builds
Docker images are automatically built and published to GitHub Container Registry:
- Push to main or staging branch → `latest` tag (main) or `staging` tag
- Version tags (v*) → versioned tags (e.g., v1.0.0, 1.0, 1)

See `.github/workflows/docker.yml` for the Docker build configuration and `doc/DEPLOYMENT.md` for usage instructions.

## Contributing Workflow

Always follow the loop for each task:
1) Propose changes → 2) Update docs → 3) Implement minimal code → 4) Add/Update tests → 5) Run quality gates and summarize

If something is out of scope for the current task, add it to `TODO.md` instead of implementing.
