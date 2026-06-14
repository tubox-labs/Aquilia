# Docker Deployment

Aquilia provides first-class Docker support through the `aq deploy` command group. The `DockerfileGenerator` introspects your workspace and generates production-optimized, multi-stage Dockerfiles with BuildKit features, non-root users, and health checks.

## Quick Start

```bash
# Generate Dockerfiles from your workspace
aq deploy dockerfile

# Generate with development Dockerfile (hot-reload)
aq deploy dockerfile --dev

# Force overwrite existing files
aq deploy dockerfile --force

# Preview without writing
aq deploy dockerfile --dry-run
```

This generates:

```
Dockerfile              # Production (multi-stage, BuildKit)
Dockerfile.dev          # Development (hot-reload, only with --dev)
.dockerignore           # Build context exclusions
```

## Generated Dockerfile Structure

The production Dockerfile uses a **multi-stage build** with the following stages:

### Stage 1: Builder

The first stage installs dependencies and compiles bytecode:

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /app

# BuildKit cache mounts for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip

# Copy dependencies first (layer caching)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user -r requirements.txt
```

### Stage 2: Artifact Compilation

If your workspace uses the Aquilia artifact system, a dedicated stage compiles artifacts:

```dockerfile
FROM builder AS artifact-compiler
COPY . .
RUN python -m aquilia compile --output-dir /app/compiled
```

### Stage 3: Production

The final stage is minimal and security-hardened:

```dockerfile
FROM python:3.12-slim AS production
WORKDIR /app

# Create non-root user
RUN groupadd -r aquilia && useradd -r -g aquilia aquilia

# Copy only what's needed
COPY --from=builder /root/.local /root/.local
COPY --from=artifact-compiler /app/compiled /app/compiled
COPY . .

# Use tini as init for proper signal handling
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/root/.local/bin:$PATH \
    AQUILIA_ENV=prod \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

USER aquilia
EXPOSE 8000

ENTRYPOINT ["tini", "--"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "--bind", "0.0.0.0:8000", "aquilia.entrypoint:create_app()"]
```

## Development Dockerfile

The dev Dockerfile includes hot-reload support:

```dockerfile
FROM python:3.12-slim AS development
WORKDIR /app

RUN pip install --upgrade pip

# Dev dependencies for hot-reload
RUN pip install uvicorn[standard]

COPY . .

ENV AQUILIA_ENV=dev \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "--factory", "aquilia.entrypoint:create_app", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Environment Variables

Essential environment variables for Docker deployments:

| Variable | Default | Description |
|----------|---------|-------------|
| `AQUILIA_ENV` | `prod` | Runtime mode: `dev`, `test`, `prod` |
| `AQUILIA_WORKSPACE` | `/app` | Workspace root path |
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |
| `DATABASE_URL` | — | Database connection string |
| `REDIS_URL` | — | Redis connection string |
| `SECRET_KEY` | — | Application secret key |

!!! warning "Production Mode"
    Always set `AQUILIA_ENV=prod` in production. This disables debug pages, enables security hardening, and ensures sensitive information is never leaked.

## Health Checks

The generated Dockerfile includes a health check that hits the `/health` endpoint:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

If your application serves a health endpoint at a different path, adjust accordingly. You can override the health check in `docker-compose.yml`:

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/custom/health"]
      interval: 15s
      timeout: 3s
      retries: 3
```

## Multi-Stage Build with BuildKit

To enable BuildKit features (cache mounts, parallel builds):

```bash
# Set BuildKit as default
export DOCKER_BUILDKIT=1

# Build
docker build -t myapp:latest .

# Or inline
DOCKER_BUILDKIT=1 docker build -t myapp:latest .
```

## `.dockerignore`

The generated `.dockerignore` excludes development files from the build context:

```gitignore
# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Development
.git/
.gitignore
.mypy_cache/
.ruff_cache/

# Documentation
docs/
*.md

# Environment
.env
.env.*
```

## Docker Compose Integration

Generate a full Docker Compose setup alongside Dockerfiles:

```bash
# Generate compose with monitoring
aq deploy compose --monitoring

# Build and run
docker compose up -d --build

# Tail logs
docker compose logs -f app

# Audit running services
docker compose ps --format table
```

The generated `docker-compose.yml` auto-detects services based on your workspace configuration:

- **Application**: Your Aquilia app with Gunicorn + Uvicorn workers
- **PostgreSQL/MySQL**: If database is configured
- **Redis**: If cache or sessions are configured
- **Nginx**: Reverse proxy with rate limiting and security headers (compose profile: `proxy`)
- **Prometheus + Grafana**: Monitoring stack (compose profile: `monitoring`)

```bash
# Start with monitoring profile
docker compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000  # admin/admin

# Access Prometheus
open http://localhost:9090
```

## Manual Build Workflow

If you prefer to build without the generator:

```bash
# Build the image
docker build -t myaquilia-app:latest .

# Run locally
docker run -p 8000:8000 \
  -e AQUILIA_ENV=prod \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  myaquilia-app:latest

# Run with volume mount for dev
docker run -p 8000:8000 \
  -v $(pwd):/app \
  -e AQUILIA_ENV=dev \
  myaquilia-app:latest
```

## Deploy to Render PaaS

Aquilia has native Render integration. Deploy your Dockerized app with a single command:

```bash
# Authenticate
aq provider login render

# Deploy
aq deploy render --image myapp:latest --region oregon --plan starter

# Check status
aq deploy render --status

# Tear down
aq deploy render --destroy
```

## Best Practices

1. **Use multi-stage builds** — keeps the final image small by excluding build dependencies.
2. **Run as non-root** — the generated Dockerfile creates an `aquilia` user.
3. **Use `tini` as init** — ensures proper signal forwarding and zombie process reaping.
4. **Pin Python version** — use a specific slim image (e.g., `python:3.12-slim`).
5. **Layer ordering** — copy `requirements.txt` first, then code, to maximize cache hits.
6. **BuildKit cache mounts** — `--mount=type=cache,target=/root/.cache/pip` speeds up repeated builds.
7. **Health checks** — always configure health checks for orchestrator integration.
8. **`.dockerignore`** — exclude `.git`, `.venv`, and development artifacts from the build context.
9. **Always set `AQUILIA_ENV=prod`** in production images.
10. **Never bake secrets into images** — use environment variables or mounted secrets files.