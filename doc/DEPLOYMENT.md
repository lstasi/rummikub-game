# Deployment

This repository can be run locally, through Docker Compose, or from the published GitHub Container Registry image.

## Runtime Targets

### Combined Application

`main.py` creates a single FastAPI app that serves:
- the static UI at `/`
- the API under `/api/v1`
- OpenAPI docs at `/docs`

### Redis Dependency

Redis is required for any stateful API operation.

Default connection string:

```text
redis://localhost:6379/0
```

## Local Development

Recommended flow:

```bash
pip install -e .[dev]
docker compose up redis -d
python main.py --reload
```

Useful flags:

```bash
python main.py --host 0.0.0.0 --port 8090 --reload
python main.py --skip-redis-check
```

`main.py` performs a Redis connectivity check unless `--skip-redis-check` is supplied.

## Docker Compose

### Full Stack

`docker-compose.yml` starts:
- `redis` using `redis:7-alpine`
- `rummikub` built from the local `Dockerfile`

Run it with:

```bash
docker compose up -d
docker compose logs -f rummikub
```

Ports:
- UI and API: `8090`
- Redis: `6379`

Health checks:
- API: `http://localhost:8090/api/v1/health`
- Redis: `redis-cli ping`

### App-Only Compose

`docker-compose.app.yml` runs only the application container and expects an external Redis instance.

Example:

```bash
REDIS_URL=redis://your-redis-host:6379/0 docker compose -f docker-compose.app.yml up -d
```

## Docker Image

The `Dockerfile`:
- uses `python:3.13-slim`
- installs dependencies from `requirements.txt`
- copies `src/`, `static/`, `scripts/`, and `main.py`
- exposes port `8090`
- runs `python main.py --host 0.0.0.0 --port 8090`

Container health check:

```text
GET /api/v1/health
```

## Published Images

GitHub Actions publishes images to `ghcr.io/lstasi/rummikub-game`.

Current workflow behavior from `.github/workflows/docker.yml`:
- Build on pushes to `main` and `staging`
- Build on tags matching `v*`
- Publish `latest` for the default branch
- Publish multi-arch images for `linux/amd64` and `linux/arm64`

Example pull:

```bash
docker pull ghcr.io/lstasi/rummikub-game:latest
```

## Environment Variables

### Application

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` in Docker, `redis://localhost:6379/0` locally | Redis connection string |
| `USE_FAKE_REDIS` | `false` | Testing-only toggle in API dependency code |

## CI/CD

### CI Workflow

`.github/workflows/ci.yml`:
- runs on pushes and PRs to `main`
- starts Redis as a service
- installs the package with dev dependencies
- runs pytest with coverage

### Docker Workflow

`.github/workflows/docker.yml`:
- logs into GHCR
- builds multi-architecture images
- pushes branch and tag-derived tags

## Troubleshooting

### Redis Connection Failures

```bash
docker compose ps redis
docker compose logs redis
```

### App Logs

```bash
docker compose logs -f rummikub
```

### Clean Restart

```bash
docker compose down
docker compose up -d --build
```

### Remove Redis Data

```bash
docker compose down -v
```

## Production Notes

- CORS is currently permissive and should be tightened before any public deployment.
- Auth is MVP-level and should be hardened before exposing the app externally.
- The current Redis lock is simple and suited to low-contention deployments.

See `doc/CODE_REVIEW.md` and `TODO.md` before treating the current setup as production-ready.
