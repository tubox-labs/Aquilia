# Production Checklist

This document covers everything needed to run Aquilia securely and reliably in production. Follow this checklist before deploying to production.

## 1. Environment Configuration

### Set Production Mode

```bash
export AQUILIA_ENV=prod
```

This is the single most important setting. `AQUILIA_ENV=prod` disables debug pages, enables security hardening, suppresses detailed error output, and activates production-optimized code paths.

```python
# workspace.py
from aquilia.config import AquilaConfig, Env

ProdEnv = AquilaConfig.for_env("production", {
    "debug": False,
    "log_level": "warning",
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
    },
})
```

!!! danger "Critical"
    Never run with `debug=True` in production. Even if accidentally set, Aquilia's debug page renderer refuses to render exception pages when it detects a production environment (`AQUILIA_ENV=prod`/`production`/`staging`).

### Validate Configuration

```bash
# Check all config values
aq validate

# Export config for inspection
aq inspect config

# Comprehensive workspace diagnostics
aq doctor
```

### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AQUILIA_ENV` | Runtime mode | `prod` |
| `SECRET_KEY` | Cryptographic signing | `openssl rand -hex 32` |
| `DATABASE_URL` | Database connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis (if used) | `redis://:password@host:6379/0` |
| `CORS_ORIGINS` | Allowed origins | `https://myapp.com,https://app.myapp.com` |

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 2. Server Configuration

### Production Server (Gunicorn + Uvicorn)

Aquilia provides the `server` extra for production deployment:

```bash
pip install aquilia[server]
```

This installs `gunicorn>=22.0.0` and `uvicorn[standard]>=0.30.0`.

### Gunicorn Configuration

```bash
gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  --bind 0.0.0.0:8000 \
  --timeout 30 \
  --graceful-timeout 10 \
  --keep-alive 5 \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --access-logfile - \
  --error-logfile - \
  --log-level warning \
  aquilia.entrypoint:create_app()
```

| Flag | Recommended Value | Purpose |
|------|------------------|---------|
| `-w` | `2-4 × CPU cores` | Worker count |
| `--timeout` | `30` | Request timeout (seconds) |
| `--graceful-timeout` | `10` | Graceful shutdown timeout |
| `--keep-alive` | `5` | Keep-alive on idle connections |
| `--max-requests` | `10000` | Restart worker after N requests (memory leak mitigation) |
| `--max-requests-jitter` | `1000` | Randomize restart threshold |
| `--log-level` | `warning` | Reduce noise in production |

### Worker Sizing

```bash
# Recommended: 2 workers per CPU core, up to a practical limit
# For a 4-core machine:
gunicorn -w 8 -k uvicorn.workers.UvicornWorker aquilia.entrypoint:create_app()
```

A good starting formula: `workers = 2 * CPU_COUNT + 1`

---

## 3. Security Headers

Aquilia can generate Nginx reverse-proxy configuration with security headers:

```bash
aq deploy nginx
```

This produces `deploy/nginx/nginx.conf` with:

### Essential Security Headers

```nginx
# HSTS (HTTP Strict Transport Security)
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;

# XSS Protection
add_header X-XSS-Protection "1; mode=block" always;

# Frame options
add_header X-Frame-Options "DENY" always;

# Content type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Referrer policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions policy
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```

### Enable in Aquilia Config

```python
ProdEnv = AquilaConfig.for_env("production", {
    "security": {
        "cors_enabled": True,
        "cors_origins": ["https://myapp.com"],
        "csrf_protection": True,
        "helmet_enabled": True,  # Security headers middleware
        "rate_limiting": True,
        "rate_limit": "100/minute",
    },
})
```

---

## 4. CORS Configuration

```python
from aquilia.config import AquilaConfig

config = AquilaConfig.for_env("production", {
    "security": {
        "cors_enabled": True,
        "cors_origins": ["https://myapp.com", "https://admin.myapp.com"],
        "cors_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "cors_headers": ["Authorization", "Content-Type", "X-Request-ID"],
        "cors_credentials": True,
        "cors_max_age": 86400,
    },
})
```

---

## 5. Rate Limiting

```python
# Global rate limit
config = AquilaConfig.for_env("production", {
    "security": {
        "rate_limiting": True,
        "rate_limit": "100/minute",       # Per IP
        "rate_limit_auth": "5/minute",     # Auth endpoints
        "rate_limit_api": "1000/hour",     # API endpoints
    },
})
```

Rate limiting can also be configured per-route with middleware or applied via Nginx:

```nginx
# Nginx rate limiting
limit_req_zone $binary_remote_addr zone=aquilia:10m rate=10r/s;

location / {
    limit_req zone=aquilia burst=20 nodelay;
    proxy_pass http://aquilia_app;
}
```

---

## 6. HTTPS / TLS

### Via Nginx (Recommended)

Place certificates in `deploy/nginx/ssl/` and uncomment the HTTPS block:

```nginx
server {
    listen 443 ssl http2;
    server_name myapp.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### Via Render

Render provides automatic HTTPS for all services. No certificate management needed — just deploy.

---

## 7. Database Configuration

### Connection Pooling

```python
config = AquilaConfig.for_env("production", {
    "database": {
        "url": "postgresql://user:pass@host:5432/db",
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "echo": False,  # Never enable SQL logging in production
    },
})
```

### Read/Write Splitting (if applicable)

```python
config = AquilaConfig.for_env("production", {
    "database": {
        "url": "postgresql://user:pass@primary-host:5432/db",
        "read_url": "postgresql://user:pass@replica-host:5432/db",
    },
})
```

### Database Migrations

Run migrations before deploying new code:

```bash
# Generate migration
aq migrate make-migrations "Add users table"

# Apply migration
aq migrate migrate

# Check migration status
aq migrate status
```

---

## 8. Cache Configuration

```python
config = AquilaConfig.for_env("production", {
    "cache": {
        "backend": "redis",
        "url": "redis://:password@redis-host:6379/0",
        "prefix": "aquilia:",
        "default_ttl": 3600,
        "stampede_protection": True,
    },
})
```

---

## 9. Session Configuration

```python
config = AquilaConfig.for_env("production", {
    "sessions": {
        "backend": "redis",
        "url": "redis://:password@redis-host:6379/1",
        "cookie_name": "_session",
        "cookie_secure": True,       # HTTPS only
        "cookie_httponly": True,     # Inaccessible to JavaScript
        "cookie_samesite": "Lax",
        "max_age": 86400,            # 24 hours
        "rotation_interval": 3600,   # Rotate session ID hourly
    },
})
```

---

## 10. Logging

### Production Logging Configuration

```python
config = AquilaConfig.for_env("production", {
    "logging": {
        "level": "warning",
        "format": "json",  # Structured JSON for log aggregation
        "handlers": ["console", "file"],
        "file": "/var/log/aquilia/app.log",
        "max_size": "100MB",
        "backup_count": 10,
    },
})
```

### Log Aggregation

Output structured JSON logs that can be ingested by:
- **Datadog**, **ELK Stack**, **Loki**, **CloudWatch**

```json
{
  "timestamp": "2026-06-14T12:00:00Z",
  "level": "warning",
  "logger": "aquilia.server",
  "message": "Request timeout",
  "context": {
    "request_id": "abc-123",
    "path": "/api/users",
    "method": "GET",
    "status": 504,
    "duration_ms": 30100
  }
}
```

---

## 11. Monitoring

### Generate Monitoring Configuration

```bash
aq deploy monitoring
```

This creates `deploy/prometheus/prometheus.yml` and `deploy/grafana/` provisioning.

### Start Monitoring Stack

```bash
docker compose --profile monitoring up -d
```

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (admin/admin)

### OpenTelemetry Tracing

```bash
pip install aquilia[otel]
```

```python
config = AquilaConfig.for_env("production", {
    "otel": {
        "enabled": True,
        "exporter": "otlp",
        "endpoint": "http://otel-collector:4317",
        "service_name": "myapp",
        "sample_rate": 0.1,  # Sample 10% of traces
    },
})
```

---

## 12. Background Tasks

```python
config = AquilaConfig.for_env("production", {
    "tasks": {
        "backend": "redis",
        "url": "redis://:password@redis-host:6379/2",
        "concurrency": 4,
        "max_retries": 3,
        "retry_delay": 60,
        "task_timeout": 300,
    },
})
```

Start the task worker:

```bash
aq run tasks
```

---

## 13. Static Files

In production, serve static files through Nginx or a CDN — not through the application server:

```nginx
location /static/ {
    alias /app/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /app/media/;
    expires 7d;
}
```

---

## 14. Backups

### Database Backups

```bash
# PostgreSQL
pg_dump -h $DATABASE_HOST -U $DATABASE_USER $DATABASE_NAME | gzip > backup-$(date +%Y%m%d).sql.gz

# Automate with cron
0 2 * * * /usr/local/bin/backup-db.sh
```

### Configuration Backups

- Store `.env` files securely (e.g., in a secrets manager)
- Version-control `workspace.py` and all module manifests
- Keep deployment configurations (`k8s/`, `docker-compose.yml`) in version control

### Volume Backups

For persistent volumes in Kubernetes, use your cloud provider's snapshot feature or Velero.

---

## 15. Scaling

### Horizontal Scaling

Aquilia is stateless by design — scale horizontally behind a load balancer:

```yaml
# Kubernetes
spec:
  replicas: 5
  template: ...
```

```bash
# Docker Compose
docker compose up -d --scale app=5
```

### Vertical Scaling

Increase resources per instance:

```yaml
# Kubernetes
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

### Auto-Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## Pre-Deployment Checklist

Run through this list before every production deployment:

- [ ] `AQUILIA_ENV=prod` is set
- [ ] `debug=False` in production config
- [ ] `SECRET_KEY` is a strong random value (>= 32 bytes)
- [ ] Database `echo=False` (no SQL logging)
- [ ] `log_level=warning` (not `debug` or `info`)
- [ ] CORS origins are restricted to known domains
- [ ] Rate limiting is enabled
- [ ] HTTPS/TLS is enabled with modern ciphers
- [ ] Security headers are configured (HSTS, CSP, X-Frame-Options, etc.)
- [ ] Session cookies are `secure=True`, `httponly=True`, `samesite=Lax`
- [ ] Health check endpoint works (`GET /health` returns 200)
- [ ] Database migrations have been applied
- [ ] Database backups are scheduled
- [ ] Monitoring is configured (Prometheus, Grafana, or OTel)
- [ ] Background task worker is running (if used)
- [ ] Static files are served via Nginx/CDN, not the app server
- [ ] Worker count is appropriate (`2 × CPU_CORES + 1`)
- [ ] Non-root user is used in Docker containers
- [ ] Health probes are configured (liveness + readiness for K8s)
- [ ] `.dockerignore` excludes development files
- [ ] `.gitignore` excludes `.env` files
- [ ] Secrets are not baked into Docker images
- [ ] All tests pass (`pytest tests/ -x -q`)
- [ ] `aq doctor` returns no critical issues

## Quick Start: Production Docker

```bash
# 1. Generate production Dockerfile
aq deploy dockerfile

# 2. Build
docker build -t myapp:latest .

# 3. Run with production settings
docker run \
  -e AQUILIA_ENV=prod \
  -e SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -p 8000:8000 \
  myapp:latest
```

## Quick Start: Production Compose

```bash
# 1. Generate compose with monitoring
aq deploy compose --monitoring

# 2. Copy and edit env
cp .env.example .env
# Edit .env with real values

# 3. Start everything
docker compose up -d
docker compose --profile monitoring up -d
docker compose logs -f app
```

## Post-Deployment Verification

```bash
# Health check
curl -f http://localhost:8000/health

# Check headers
curl -I https://myapp.com | grep -E "strict-transport|x-frame|x-content|x-xss"

# Run diagnostics
aq doctor

# Check service status (Render)
aq deploy render --status

# Check K8s
kubectl get pods -n myapp
kubectl describe deployment myapp -n myapp
```