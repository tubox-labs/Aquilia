# Aquilia — Observability & Monitoring

> Logging, tracing, health checks, metrics, error tracking, and admin monitoring.

---

## Overview

Aquilia provides multi-layered observability through built-in health checks, structured error tracking, admin monitoring panels, query inspection, request lifecycle tracing, and integration hooks for external monitoring systems.

---

## 1. Health Check Registry

**Location:** `aquilia/health.py`

The `HealthRegistry` is a centralized health check system that aggregates subsystem status.

### Architecture

```
HealthRegistry
├── register(name, checker)          # Register a health check function
├── check_all()                      # Run all checks, return aggregate status
└── to_dict()                        # Serialize for HTTP response
```

### Registered Checks

| Check | What It Verifies | Registered By |
|-------|-----------------|---------------|
| `database` | DB connection alive, pool status | `db/engine.py` |
| `cache` | Cache backend reachable | `cache/base.py` |
| `redis` | Redis PING response | `cache/backends/redis.py` |
| `mail` | SMTP/SES connectivity | `mail/manager.py` |
| `task_queue` | Worker thread alive | `tasks/queue.py` |
| `session_store` | Session backend read/write | `sessions/engine.py` |

### Health Response Format

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 2.3},
    "cache": {"status": "healthy", "latency_ms": 0.4},
    "redis": {"status": "degraded", "error": "high latency"},
    "mail": {"status": "unhealthy", "error": "connection refused"}
  }
}
```

### Aggregate Status Logic

```
All healthy         → "healthy"
Any degraded        → "degraded" (HTTP 200)
Any unhealthy       → "unhealthy" (HTTP 503)
Check raises error  → "unhealthy" for that check
```

### Endpoint

Health checks are exposed at `/health` (configurable) via:
- **Admin panel:** `/admin/health` (authenticated)
- **Server-level:** `AqServer.health_route` → registered during `_register_internal_routes()`

---

## 2. Structured Logging

### Framework Logging Pattern

Aquilia uses Python's `logging` module consistently across all subsystems:

```python
import logging
logger = logging.getLogger(__name__)
```

### Log Points by Subsystem

| Subsystem | Log Level | What Is Logged |
|-----------|-----------|---------------|
| `server.py` | INFO | Server startup, shutdown, route registration, middleware stack |
| `server.py` | DEBUG | Request lifecycle phases, middleware execution order |
| `server.py` | WARNING | Deprecated features, fallback behaviors |
| `server.py` | ERROR | Unhandled exceptions, startup failures |
| `middleware.py` | DEBUG | Each middleware invocation, timing |
| `controller/router.py` | DEBUG | Route matching, parameter extraction |
| `controller/executor.py` | ERROR | Handler exceptions, content negotiation failures |
| `db/engine.py` | INFO | Connection pool created, migrations applied |
| `db/engine.py` | DEBUG | Query execution with timing |
| `db/engine.py` | ERROR | Connection failures, query errors |
| `cache/` | DEBUG | Cache hits/misses, evictions, stampede prevention |
| `auth/` | INFO | Login success, token issued, MFA enrolled |
| `auth/` | WARNING | Failed login, expired token, suspicious activity |
| `auth/` | CRITICAL | Account lockout, brute-force detected |
| `di/container.py` | DEBUG | Provider resolution, scope transitions |
| `di/container.py` | WARNING | Circular dependency detection, missing providers |
| `tasks/queue.py` | INFO | Task enqueued, started, completed |
| `tasks/queue.py` | ERROR | Task failed, moved to dead letter |
| `mail/` | INFO | Email sent, provider selected |
| `mail/` | ERROR | Send failure, provider fallback |
| `build/pipeline.py` | INFO | Build phase transitions, artifact fingerprints |
| `cli/` | INFO | Command execution, migration status |
| `mlops/` | INFO | Model loaded, inference served, drift detected |

### Configuration

Logging is configurable through:

1. **Application config:** `AqServer.configure()` accepts logging settings
2. **YAML config:** `config.yaml` → `logging:` section
3. **CLI:** `aq serve --log-level debug`

---

## 3. Error Tracking

### Fault Engine

**Location:** `aquilia/faults/`

The fault system provides structured error classification, propagation, and tracking.

```
FaultEngine
├── Fault (base class)
│   ├── code: str                    # e.g., "AUTH_001"
│   ├── message: str                 # Human-readable
│   ├── severity: FaultSeverity      # LOW / MEDIUM / HIGH / CRITICAL
│   ├── context: dict                # Structured metadata
│   └── chain: List[Fault]           # Causal chain
├── FaultHandler (Chain of Responsibility)
│   ├── LoggingHandler               # Log to Python logger
│   ├── MetricsHandler               # Increment error counters
│   ├── NotificationHandler          # Alert on CRITICAL
│   └── RecoveryHandler              # Attempt auto-recovery
└── FaultRegistry
    ├── register(fault_class)
    └── lookup(code) → FaultClass
```

### Fault Categories

| Domain | Code Prefix | Example Codes |
|--------|-------------|---------------|
| Auth | `AUTH_` | `AUTH_001` (invalid credentials), `AUTH_040` (MFA required) |
| Database | `DB_` | `DB_001` (connection failed), `DB_010` (migration error) |
| Cache | `CACHE_` | `CACHE_001` (backend unreachable) |
| Validation | `VAL_` | `VAL_001` (field required), `VAL_020` (type mismatch) |
| HTTP | `HTTP_` | `HTTP_404` (not found), `HTTP_429` (rate limited) |
| DI | `DI_` | `DI_001` (circular dependency), `DI_010` (missing provider) |
| Task | `TASK_` | `TASK_001` (execution failed), `TASK_010` (dead letter) |

### Admin Error Tracker

**Location:** `aquilia/admin/controller.py` — error tracking routes

The admin panel includes a built-in error tracker:

| Route | Function |
|-------|----------|
| `GET /admin/errors` | List recent errors with pagination |
| `GET /admin/errors/{id}` | Error detail with full stack trace |
| `POST /admin/errors/{id}/resolve` | Mark error as resolved |
| `GET /admin/errors/stats` | Error frequency, top errors, trends |

---

## 4. Admin Monitoring Dashboard

**Location:** `aquilia/admin/site.py`, `aquilia/admin/controller.py`

### System Information Panel

```
GET /admin/system
```

Returns:
- Python version, OS, platform
- Aquilia version, debug mode status
- Registered modules count
- Database backend and connection status
- Cache backend status
- Active sessions count

### Query Inspector

```
GET /admin/queries
```

The admin panel includes a SQL query inspector that:
- Records all SQL queries executed per request
- Shows query timing, parameters, and execution plan
- Highlights N+1 query patterns
- Shows slow query aggregation

### Route Inspector

```
GET /admin/routes
```

Lists all registered routes with:
- URL pattern
- HTTP methods
- Controller and handler function
- Applied middleware
- Authentication requirements
- Rate limit configuration

### Middleware Inspector

```
GET /admin/middleware
```

Displays the middleware stack with:
- Execution order
- Middleware class names
- Configuration parameters

---

## 5. Request Lifecycle Tracing

### Timing Middleware

**Location:** `aquilia/middleware.py`

The request execution flow tracks timing at each phase:

```
Request Start
│
├─ Middleware Stack (outer → inner)          ← timed
│   ├─ CORSMiddleware
│   ├─ CSRFMiddleware
│   ├─ SessionMiddleware
│   ├─ AuthMiddleware
│   ├─ CacheMiddleware
│   └─ Custom middleware
│
├─ Route Matching                            ← timed
│   └─ Router.match(path, method)
│
├─ Flow Pipeline (12-phase executor)         ← timed per phase
│   ├─ Guard execution
│   ├─ Parameter binding
│   ├─ Body parsing
│   ├─ Validation
│   ├─ Handler execution
│   └─ Response serialization
│
├─ Middleware Stack (inner → outer)          ← timed
│
Response End
```

### Server Timing Headers

The response includes `Server-Timing` header:

```
Server-Timing: total;dur=45.2, route;dur=0.3, handler;dur=12.1, db;dur=8.4
```

---

## 6. Database Monitoring

### Connection Pool Metrics

**Location:** `aquilia/db/engine.py`

The database engine tracks:
- Pool size (current / max)
- Active connections
- Idle connections
- Wait count (connections queued)
- Connection creation/destruction events

### Query Logging

**Location:** `aquilia/db/adapters/` — all adapters

Each adapter logs:
- Query text (with parameters masked)
- Execution duration
- Rows affected/returned
- Transaction state (in transaction, savepoint depth)

### Migration Tracking

**Location:** `aquilia/models/migrations/`

The migration system logs:
- Migration applied/rolled back
- Execution duration
- Schema changes (table created, column added, index built)
- Rename detection decisions (Levenshtein similarity scores)

---

## 7. Cache Monitoring

### Cache Stats

**Location:** `aquilia/cache/backends/`

Each cache backend tracks:
- Hit rate / miss rate
- Total gets / sets / deletes
- Eviction count (by policy: LRU, LFU, FIFO, TTL, Random)
- Average latency
- Memory usage (memory backend)
- Stampede prevention activations

### Cache Admin Panel

```
GET /admin/cache
```

Displays:
- Backend type and configuration
- Hit/miss ratio
- Key count
- Memory usage
- Recent evictions

---

## 8. Task Queue Monitoring

### Queue Metrics

**Location:** `aquilia/tasks/queue.py`

The task queue tracks:
- Pending tasks count (by priority)
- Running tasks count
- Completed tasks count
- Failed tasks count
- Dead letter queue size
- Average execution time
- Retry count distribution

### Task Admin Panel

```
GET /admin/tasks
```

Displays:
- Active workers
- Queue depth by priority
- Recent task executions (success/failure)
- Dead letter queue contents
- Scheduled tasks (cron/interval)

---

## 9. MLOps Monitoring

**Location:** `aquilia/mlops/`

### Model Serving Metrics

| Metric | Description |
|--------|-------------|
| `inference_count` | Total inferences served |
| `inference_latency_ms` | P50/P95/P99 latency |
| `model_load_time_ms` | Time to load model into memory |
| `model_size_bytes` | Model artifact size |
| `batch_size` | Average batch size |
| `error_rate` | Failed inference percentage |

### Drift Detection

The drift detection system (`aquilia/mlops/monitoring/drift/`) monitors:
- Feature distribution shifts (KS test, PSI, chi-squared)
- Prediction distribution changes
- Input data quality (missing values, out-of-range)
- Alert thresholds with configurable sensitivity

### A/B Test Monitoring

```
GET /admin/mlops/experiments
```

Tracks:
- Traffic split ratios
- Per-variant metrics
- Statistical significance
- Canary rollout status

---

## 10. Auth & Session Monitoring

### Auth Events

The auth system emits structured events via the OWASP audit trail (`aquilia/auth/audit.py`):

| Event | Fields Logged |
|-------|--------------|
| `LOGIN_SUCCESS` | user_id, ip, user_agent, timestamp |
| `LOGIN_FAILURE` | attempted_username, ip, reason, attempt_count |
| `LOGOUT` | user_id, session_id, timestamp |
| `TOKEN_ISSUED` | user_id, token_type, expiry |
| `TOKEN_REVOKED` | user_id, token_id, reason |
| `MFA_ENROLLED` | user_id, method (TOTP/WebAuthn) |
| `MFA_VERIFIED` | user_id, method |
| `MFA_FAILED` | user_id, method, attempt_count |
| `ACCOUNT_LOCKED` | user_id, reason, lockout_duration |
| `PASSWORD_CHANGED` | user_id, timestamp |
| `PERMISSION_DENIED` | user_id, resource, action |

### Session Analytics

```
GET /admin/sessions
```

Shows:
- Active session count
- Session duration distribution
- Sessions by user agent
- Geographic distribution (if IP geolocation available)
- Session store backend status

---

## 11. WebSocket Monitoring

**Location:** `aquilia/sockets/`

The WebSocket system tracks:
- Active connections count
- Messages sent/received per second
- Connection duration
- Room membership
- Redis pub/sub channel subscriptions (when using Redis adapter)

---

## 12. Integration Points

### External Monitoring Integration

Aquilia's observability data can be exported to external systems:

| System | Integration Method |
|--------|--------------------|
| **Prometheus** | Health endpoint scraping, custom metrics middleware |
| **Grafana** | Via Prometheus/InfluxDB data source |
| **Sentry** | Fault engine hook → Sentry SDK |
| **ELK Stack** | Structured JSON logging → Logstash |
| **Datadog** | Custom middleware + DogStatsD |
| **New Relic** | Agent auto-instrumentation + custom attributes |
| **AWS CloudWatch** | Structured logging to stdout → CloudWatch agent |

### Custom Monitoring Hooks

The `EffectManager` and `subsystem` protocol allow registering custom monitoring:

```python
class MonitoringSubsystem(BaseSubsystem):
    async def startup(self):
        self.app.effects.register("request.start", self.on_request_start)
        self.app.effects.register("request.end", self.on_request_end)
        self.app.effects.register("db.query", self.on_query)

    async def on_request_start(self, request):
        # Custom metrics collection
        ...
```

---

## 13. Diagnostic Endpoints Summary

| Endpoint | Auth Required | Description |
|----------|--------------|-------------|
| `/health` | No | Public health check |
| `/admin/system` | Admin | System information |
| `/admin/health` | Admin | Detailed health with history |
| `/admin/routes` | Admin | Route inspector |
| `/admin/middleware` | Admin | Middleware stack |
| `/admin/queries` | Admin | SQL query inspector |
| `/admin/errors` | Admin | Error tracker |
| `/admin/cache` | Admin | Cache stats |
| `/admin/tasks` | Admin | Task queue monitor |
| `/admin/sessions` | Admin | Session analytics |
| `/admin/mlops/experiments` | Admin | ML experiment tracker |
