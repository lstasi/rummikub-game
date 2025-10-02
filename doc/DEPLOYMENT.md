# Deployment

This document describes how to deploy and run the Rummikub game application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

To run the complete application stack (API + Redis):

```bash
# Clone the repository
git clone <repository-url>
cd rummikub-game

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

The API will be available at:
- **API Endpoints**: http://localhost:8090
- **API Documentation**: http://localhost:8090/docs
- **ReDoc Documentation**: http://localhost:8090/redoc
- **Health Check**: http://localhost:8090/health

## Using Pre-built Docker Images

Pre-built Docker images are automatically published to GitHub Container Registry (ghcr.io) on each push to the main branch and for tagged releases.

### Pull and Run Pre-built Image

```bash
# Pull the latest image
docker pull ghcr.io/lstasi/rummikub-game:latest

# Run with Redis
docker run -d --name rummikub-redis redis:7-alpine
docker run -d --name rummikub-api -p 8090:8090 \
  -e REDIS_URL=redis://rummikub-redis:6379/0 \
  --link rummikub-redis:redis \
  ghcr.io/lstasi/rummikub-game:latest
```

### Using Tagged Versions

```bash
# Pull a specific version
docker pull ghcr.io/lstasi/rummikub-game:v1.0.0

# Or use major/minor tags
docker pull ghcr.io/lstasi/rummikub-game:1.0
docker pull ghcr.io/lstasi/rummikub-game:1
```

### Automated Builds

Docker images are automatically built and pushed by GitHub Actions:
- **Workflow**: `.github/workflows/docker.yml`
- **Triggers**: Push to main branch, tag creation (v*)
- **Registry**: GitHub Container Registry (ghcr.io)
- **Tags**: 
  - `latest` - Latest build from main branch
  - `v{version}` - Specific version tags (e.g., v1.0.0)
  - `{major}.{minor}` - Major/minor version tags (e.g., 1.0)
  - `{major}` - Major version tag (e.g., 1)

## Services

### API Service (`api`)

The FastAPI application serving the game REST endpoints.

- **Image**: Built from local Dockerfile
- **Port**: 8090 (mapped to host port 8090)
- **Health Check**: GET /health endpoint
- **Dependencies**: Redis service

### Redis Service (`redis`)

Redis server for game state persistence.

- **Image**: redis:7-alpine
- **Port**: 6379 (mapped to host port 6379)
- **Data Persistence**: Uses named volume `redis_data`
- **Configuration**: Append-only file (AOF) enabled
- **Health Check**: Redis PING command

## Environment Variables

### API Service

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |

### Customization

Create a `.env` file in the project root to override defaults:

```bash
# .env file example
REDIS_URL=redis://redis:6379/1
```

Then use:
```bash
docker compose --env-file .env up
```

## App-Only Deployment

For environments where Redis is already deployed separately (e.g., existing infrastructure), use the app-only compose file:

```bash
# Set Redis URL to your existing Redis instance
export REDIS_URL=redis://your-redis-host:6379/0

# Start only the API service
docker compose -f docker-compose.app.yml up -d

# Or provide Redis URL inline
REDIS_URL=redis://your-redis-host:6379/0 docker compose -f docker-compose.app.yml up -d
```

The `docker-compose.app.yml` file deploys only the API service without Redis, assuming Redis is already available.

## Development Setup

### Option 1: Using main.py (Recommended)

For local development with hot-reload:

```bash
# Install dependencies locally
pip install -e .[dev]

# Run Redis in Docker
docker compose up redis -d

# Run API locally with hot reload (defaults to port 8090)
python main.py --reload

# Or run on a different port
python main.py --reload --port 8080

# Or allow external connections
python main.py --reload --host 0.0.0.0
```

The `main.py` script provides:
- Automatic Redis connection checking
- Hot reload support for development
- Configurable host and port (defaults to 8090)
- Helpful error messages and setup instructions

### Option 2: Using uvicorn directly

```bash
# Install dependencies locally
pip install -e .[dev]

# Run Redis in Docker
docker compose up redis -d

# Run API locally with auto-reload
REDIS_URL=redis://localhost:6379/0 uvicorn rummikub.api:app --reload --host 0.0.0.0 --port 8090
```

## Production Considerations

### Security

1. **CORS Configuration**: Update CORS settings in `src/rummikub/api/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specify allowed origins
       allow_credentials=True,
       allow_methods=["GET", "POST"],  # Restrict methods
       allow_headers=["*"],
   )
   ```

2. **Redis Security**: Configure Redis authentication:
   ```yaml
   # docker compose.yml
   redis:
     command: redis-server --requirepass yourpassword --appendonly yes
   ```

3. **Environment Variables**: Use Docker secrets or external secret management.

### Scaling

To run multiple API instances:

```bash
docker compose up --scale api=3
```

Consider using a load balancer (nginx, traefik) for production deployments.

### Monitoring

Health check endpoints are configured for both services:
- API: `GET /health`
- Redis: `redis-cli ping`

Use these for orchestrator health checks (Kubernetes, Docker Swarm).

## Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Check what's using the port
   lsof -i :8090
   # Kill the process or change the port mapping
   docker compose -f docker compose.yml up
   ```

2. **Redis Connection Failed**:
   ```bash
   # Check Redis service status
   docker compose ps redis
   # View Redis logs
   docker compose logs redis
   ```

3. **API Service Won't Start**:
   ```bash
   # View API logs
   docker compose logs api
   # Rebuild the image
   docker compose build api
   ```

### Logs and Debugging

```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View specific service logs
docker compose logs api
docker compose logs redis

# Execute commands in running containers
docker compose exec api bash
docker compose exec redis redis-cli
```

### Data Management

```bash
# Backup Redis data
docker compose exec redis redis-cli BGSAVE

# View Redis data volume
docker volume inspect rummikub-game_redis_data

# Remove all data (destructive)
docker compose down -v
```

## Testing in Docker

Run tests against the containerized services:

```bash
# Start services
docker compose up -d

# Wait for services to be healthy
docker compose ps

# Run tests against containerized API
REDIS_URL=redis://localhost:6379/0 pytest tests/

# Cleanup
docker compose down
```
