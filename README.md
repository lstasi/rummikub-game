# Rummikub Game

Python-based Rummikub game with Redis backend, FastAPI API, and pytest tests. Designed for containerized runs via Docker Compose.

## Status

Completed:
- Copilot instructions with strict workflow (`COPILOT_INSTRUCTIONS.md`)
- Base project scaffolding (`src/`, `tests/`, `doc/`, `pyproject.toml`, `pytest.ini`)
- Domain model definitions documented (`doc/MODELS.md`)

Pending (see `TODO.md` for the full list):
- Implement models package + unit tests
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

- Python >= 3.11, Pydantic, FastAPI, Redis
- pytest for testing
- Docker + docker-compose for local runs

## Contributing Workflow

Always follow the loop for each task:
1) Propose changes → 2) Update docs → 3) Implement minimal code → 4) Add/Update tests → 5) Run quality gates and summarize

If something is out of scope for the current task, add it to `TODO.md` instead of implementing.
