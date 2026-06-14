# Workflows

This page documents the four key system workflows as Mermaid sequence diagrams, showing the exact component interactions at each step.

---

## Authentication Flow

Password-based authentication with token issuance, session creation, and optional MFA.

```mermaid
sequenceDiagram
    participant Client
    participant Adapter as ASGIAdapter
    participant Chain as Middleware Chain
    participant Router as ControllerRouter
    participant Engine as ControllerEngine
    participant Ctrl as AuthController
    participant AuthMgr as AuthManager
    participant Identity as IdentityStore
    participant Creds as CredentialStore
    participant Hasher as PasswordHasher
    participant Tokens as TokenManager
    participant Session as SessionEngine

    Client->>Adapter: POST /auth/login {identity, password}
    Adapter->>Chain: Execute middleware pipeline
    Chain->>Chain: FaultMiddleware wraps
    Chain->>Chain: CORS check
    Chain->>Chain: Rate limit check
    Chain->>Router: Route match
    Router-->>Chain: ControllerRouteMatch
    Chain->>Engine: execute(route, request, params, container)
    Engine->>Ctrl: await handler(request, ctx, body)

    Ctrl->>AuthMgr: authenticate_password(identity_id, password)
    AuthMgr->>RateLimiter: check lockout(identity_id)
    alt Account locked
        AuthMgr-->>Ctrl: AUTH_ACCOUNT_LOCKED fault
    end

    AuthMgr->>Identity: get_identity(identity_id)
    Identity-->>AuthMgr: Identity | None
    alt Not found
        AuthMgr->>RateLimiter: record_attempt(identity_id)
        AuthMgr-->>Ctrl: AUTH_INVALID_CREDENTIALS fault
    end

    AuthMgr->>Identity: check status
    alt Suspended
        AuthMgr-->>Ctrl: AUTH_ACCOUNT_SUSPENDED fault
    end

    AuthMgr->>Creds: get_password_credential(identity_id)
    Creds-->>AuthMgr: PasswordCredential

    AuthMgr->>Hasher: verify(password, credential.password_hash)
    alt Wrong password
        AuthMgr->>RateLimiter: record_attempt(identity_id)
        AuthMgr-->>Ctrl: AUTH_INVALID_CREDENTIALS fault
    end

    alt MFA enabled
        AuthMgr-->>Ctrl: AUTH_MFA_REQUIRED {mfa_token, methods}
        Ctrl-->>Client: 200 {mfa_required: true, mfa_token}

        Client->>Ctrl: POST /auth/mfa/verify {mfa_token, code}
        Ctrl->>AuthMgr: verify_mfa(identity_id, code)
        AuthMgr-->>Ctrl: bool
    end

    AuthMgr->>Tokens: issue_tokens(identity_id)
    Note over Tokens: Creates access_token (JWT, HS256)<br/>+ refresh_token
    Tokens-->>AuthMgr: (access_token, refresh_token)

    AuthMgr->>Session: Engine.create_session(identity_id, scope=user)
    Session-->>AuthMgr: session_id

    AuthMgr-->>Ctrl: AuthResult(success=True, tokens, session)
    Ctrl-->>Client: Set-Cookie + JSON {access_token, refresh_token, identity}
```

### Auth Middleware (Per-Request)

```mermaid
sequenceDiagram
    participant Client
    participant Adapter as ASGIAdapter
    participant AuthMW as AuthMiddleware
    participant Session as SessionEngine
    participant AuthMgr as AuthManager
    participant Tokens as TokenManager
    participant Ctrl as Controller

    Client->>Adapter: GET /users/me (with cookies/Authorization)
    Adapter->>AuthMW: Request enters middleware
    AuthMW->>Session: Load session from cookie/header
    Session-->>AuthMW: SessionData | None

    alt Authorization header present
        AuthMW->>AuthMgr: verify_access_token(token)
        AuthMgr->>Tokens: verify(token, key_ring)
        Tokens-->>AuthMgr: TokenClaims
        AuthMgr->>Identity: get_identity(claims.sub)
        Identity-->>AuthMgr: Identity
        AuthMgr-->>AuthMW: Identity + claims
    else Session present
        AuthMW->>AuthMgr: get_identity(session.identity_id)
        AuthMgr-->>AuthMW: Identity
    else No credentials
        alt require_auth_by_default
            AuthMW-->>Client: 401 Unauthorized
        else
            AuthMW->>Ctrl: Anonymous request (identity=None)
        end
    end

    AuthMW->>Ctrl: ctx.identity = identity
    Ctrl-->>Client: Response
```

---

## Request Pipeline

The complete HTTP request lifecycle from ASGI event to response.

```mermaid
sequenceDiagram
    participant Uvicorn
    participant Adapter as ASGIAdapter
    participant MS as MiddlewareStack
    participant FM as FaultMiddleware
    participant VM as VersionMiddleware
    participant AM as AuthMiddleware
    participant CORS as CORSMiddleware
    participant RL as RateLimitMiddleware
    participant I18n as I18nMiddleware
    participant Router as ControllerRouter
    participant Engine as ControllerEngine
    participant Factory as ControllerFactory
    participant DI as DI Container
    participant Ctrl as Controller
    participant Response

    Uvicorn->>Adapter: __call__(scope, receive, send)
    Adapter->>Adapter: _build_cached_chain() (once)

    Note over Adapter: Create Request from ASGI scope
    Adapter->>Adapter: Request(scope, receive)

    Note over Adapter: Pre-resolve API version from path
    Adapter->>Adapter: _resolve_route_inputs(request, path)

    Note over Adapter: Sync route matching (O(1) or O(k))
    Adapter->>Router: match_sync(path, method, api_version)
    Router->>Router: Check _static_routes[method][path]
    alt Static match
        Router-->>Adapter: ControllerRouteMatch
    else
        Router->>Router: Walk _tries[method] segment trie
        Router-->>Adapter: ControllerRouteMatch
    end

    Note over Adapter: Create request-scoped DI container
    Adapter->>DI: app_container.create_request_scope()
    DI-->>Adapter: Request-scoped Container

    Note over Adapter: Acquire RequestCtx from pool
    Adapter->>Adapter: _ctx_pool.acquire(request, container)

    Note over Adapter: Store match in request.state
    Adapter->>Adapter: request.state["_controller_match"] = match

    Note over Adapter: Execute middleware chain
    Adapter->>FM: handler(request, ctx)

    FM->>FM: Try: wrap entire chain
    FM->>AM: next_handler(request, ctx)

    AM->>AM: Resolve identity from session/token
    AM->>AM: Set ctx.identity

    AM->>CORS: next_handler
    CORS->>CORS: Check Origin header / Preflight
    alt Preflight OPTIONS
        CORS-->>Adapter: 204 + CORS headers
    end

    CORS->>RL: next_handler
    RL->>RL: Check rate limit counters
    alt Rate limited
        RL-->>Adapter: 429 Too Many Requests
    end

    RL->>I18n: next_handler
    I18n->>I18n: Resolve locale from header/cookie/query
    I18n->>I18n: Set ctx.locale

    I18n->>MS: ... remaining middleware ...
    MS->>MS: Final handler (dispatches to controller)

    MS->>Engine: execute(route, request, path_params, container)

    Engine->>Engine: Check @clearance requirements
    alt Clearance denied
        Engine-->>MS: 403 Forbidden fault
    end

    Engine->>Factory: get_instance(controller_class, container)
    Factory->>DI: Resolve constructor dependencies
    DI-->>Factory: Controller instance

    Engine->>Engine: Build handler kwargs
    Note over Engine: Path params + query + body +<br/>DI-injected services

    Engine->>Engine: Execute @before_request interceptors
    Engine->>Ctrl: await handler(**kwargs)

    Note over Ctrl: Business logic execution

    Ctrl-->>Engine: Response object
    Engine->>Engine: Execute @after_response hooks
    Engine-->>MS: Response

    MS->>I18n: Response unwinds
    I18n->>RL: Response unwinds
    RL->>CORS: Response unwinds (add CORS headers)
    CORS->>AM: Response unwinds
    AM->>FM: Response unwinds

    alt Exception occurred
        FM->>FM: FaultEngine.process(fault)
        FM->>FM: Map to HTTP status + structured error
        FM-->>Adapter: Error Response
    end

    FM-->>Adapter: Response

    Adapter->>Adapter: _ctx_pool.release(ctx)
    Note over Adapter: DI container shutdown<br/>handled by request_scope_mw (priority 5)

    Adapter->>Response: response.send_asgi(send, request)
    Response->>Uvicorn: ASGI send events
```

### Error Handling in the Pipeline

The `FaultMiddleware` (priority 2) wraps the entire chain. When any middleware or controller raises a `Fault`:

1. `FaultMiddleware` catches the fault
2. Passes it to `FaultEngine.process(fault, app=app_name)`
3. `FaultEngine` runs registered handlers (logging, metrics, error tracker)
4. The fault is converted to an HTTP response:
    - **HTML clients:** Rendered Tubox error page (debug: stack traces; prod: sanitised)
    - **API clients:** Structured JSON `{"error": {"code": "...", "message": "...", "status": N}}`

The `request_scope_mw` (priority 5) has a `finally` block that always runs (even during exceptions, because `FaultMiddleware` catches them first) to ensure DI container cleanup.

---

## Background Task Execution

How tasks are defined, enqueued, scheduled, executed, and monitored.

```mermaid
sequenceDiagram
    participant Module as Module's tasks.py
    participant Registry as TaskRegistry
    participant Manager as TaskManager
    participant Worker as Worker Pool
    participant Backend as MemoryBackend
    participant DLQ as Dead Letter Queue
    participant FE as FaultEngine

    Note over Module,Registry: Registration Phase (startup)
    Module->>Registry: @task decorator registers function
    Registry->>Registry: Store TaskDescriptor(name, func, queue, retries)
    Manager->>Registry: Discover all registered tasks
    Manager->>Manager: Register tasks for scheduling

    Note over Manager,Backend: Runtime Phase
    Manager->>Worker: Start worker pool (num_workers=4)
    loop Each worker
        Worker->>Worker: Poll queue for jobs
    end

    Note over Module,Manager: Enqueue Phase (from controller/effect)
    Module->>Manager: enqueue("send_email", user_id="123")
    Manager->>Manager: Create Job(id, name, args, kwargs, retries, status=pending)
    Manager->>Backend: store_job(job)
    Backend-->>Manager: job_id

    Note over Worker,DLQ: Execution Phase
    Worker->>Backend: dequeue(queue="default")
    Backend-->>Worker: Job | None
    alt Job available
        Worker->>Worker: Resolve task function from registry
        Worker->>Worker: Execute task(*args, **kwargs)
        alt Success
            Worker->>Backend: mark_complete(job_id)
        else Failure
            alt Retries remaining
                Worker->>Backend: schedule_retry(job_id, retry_delay)
            else Exhausted retries
                Worker->>Backend: mark_dead_letter(job_id)
                Worker->>DLQ: on_dead_letter callback
                DLQ->>FE: fault_engine.process(TASK_DEAD_LETTER fault)
                FE->>FE: Log + metrics + error tracker
            end
        end
    end

    Note over Manager: Cron/Interval Scheduling
    Manager->>Manager: Scheduler loop
    loop Check schedules
        Manager->>Registry: Get tasks with @task(interval=...) or @task(schedule=...)
        alt Due for execution
            Manager->>Manager: enqueue(task_name)
        end
    end

    Note over Manager: Shutdown Phase
    Manager->>Manager: Set shutdown flag
    Manager->>Worker: Signal workers to drain
    Worker->>Worker: Finish current job
    Worker->>Worker: Exit loop
    Manager->>Manager: Cleanup completed jobs older than cleanup_max_age
```

### Task Decorator API

```python
@task(
    queue="priority",           # Queue name (default: "default")
    retries=3,                  # Max retry attempts
    retry_delay=60,             # Seconds between retries
    retry_backoff=2.0,          # Exponential backoff multiplier
    timeout=300,                # Max execution time in seconds
    priority=5,                 # 1-10 (higher = more urgent)
)
async def process_order(order_id: str) -> dict:
    ...

@task(interval=Interval(minutes=30))
async def hourly_cleanup() -> None:
    ...

@task(schedule=CronSchedule(minute="0", hour="2"))
async def nightly_report() -> None:
    ...
```

---

## Migration Workflow

Database schema management with migration generation, application, and rollback.

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CLI as aq CLI
    participant Scanner as Model Scanner
    participant ORM as Model Registry
    participant Gen as MigrationGenerator
    participant DB as Database
    participant FS as Filesystem

    Note over Dev,FS: Making Migrations
    Dev->>CLI: aq migrate makemigrations
    CLI->>Scanner: Scan models/ for Model subclasses
    Scanner->>ORM: Read current model definitions
    ORM-->>Scanner: Model metadata (fields, indexes, constraints)

    CLI->>DB: Read current schema state
    DB-->>CLI: Schema snapshot (tables, columns, indexes)

    CLI->>Gen: Compare: desired vs current
    Gen->>Gen: Detect changes:
    Note over Gen: - New models → CREATE TABLE<br/>- New fields → ADD COLUMN<br/>- Modified fields → ALTER COLUMN<br/>- Removed fields → DROP COLUMN<br/>- New indexes → CREATE INDEX

    Gen->>FS: Write migration file
    Note over FS: migrations/0002_add_email_verified.py
    FS-->>CLI: Migration file path

    Note over Dev,DB: Applying Migrations
    Dev->>CLI: aq migrate migrate
    CLI->>DB: Read applied migrations table
    DB-->>CLI: List of applied migration IDs

    CLI->>FS: Read pending migration files
    FS-->>CLI: Ordered list of unapplied migrations

    loop For each pending migration
        CLI->>DB: BEGIN TRANSACTION
        CLI->>DB: Execute migration SQL
        alt Success
            CLI->>DB: Record migration ID as applied
            CLI->>DB: COMMIT
        else Failure
            CLI->>DB: ROLLBACK
            CLI-->>Dev: Migration error (halt)
        end
    end

    Note over Dev,DB: Inspecting State
    Dev->>CLI: aq migrate status
    CLI->>DB: Query applied migrations
    DB-->>CLI: Applied list
    CLI->>FS: List migration files
    FS-->>CLI: Available list
    CLI-->>Dev: [✓] 0001_initial
    CLI-->>Dev: [✓] 0002_add_email_verified
    CLI-->>Dev: [ ] 0003_create_sessions (pending)

    Note over Dev,DB: SQL Preview
    Dev->>CLI: aq migrate sqlmigrate 0003
    CLI->>FS: Read migration file
    FS-->>CLI: Migration source
    CLI->>Gen: Generate SQL without executing
    Gen-->>CLI: Rendered SQL
    CLI-->>Dev: Preview SQL in terminal

    Note over Dev,DB: Introspection
    Dev->>CLI: aq migrate inspectdb
    CLI->>DB: Read schema from database
    DB-->>CLI: Current schema
    CLI->>CLI: Reverse-engineer model definitions
    CLI-->>Dev: Generated models.py
```

### Migration File Structure

```python
# migrations/0002_add_email_verified.py
from aquilia.db.migrations import Migration, operations

class Migration:
    dependencies = ["0001_initial"]

    operations = [
        operations.AddField(
            model="User",
            name="email_verified",
            field=operations.BooleanField(default=False),
        ),
        operations.AddField(
            model="User",
            name="verified_at",
            field=operations.DateTimeField(null=True),
        ),
        operations.CreateIndex(
            model="User",
            name="idx_user_email_verified",
            fields=["email_verified"],
        ),
    ]
```

---

## Deployment Workflow

End-to-end deployment pipeline from workspace to production.

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CLI as aq CLI
    participant WS as Workspace
    participant Gen as Deploy Generators
    participant FS as Filesystem Output
    participant Registry as Container Registry
    participant Render as Render Cloud
    participant K8s as Kubernetes
    participant Monitor as Prometheus/Grafana

    Note over Dev,FS: Artefact Generation
    Dev->>CLI: aq deploy all
    CLI->>WS: Read workspace.py + module manifests
    WS-->>CLI: App config, dependencies, enabled integrations

    CLI->>Gen: Generate Dockerfile
    Gen->>FS: Dockerfile
    Note over FS: Multi-stage build<br/>Python 3.10+ base<br/>pip install -e .<br/>uvicorn aquilia.entrypoint:app

    CLI->>Gen: Generate docker-compose.yml
    Gen->>FS: docker-compose.yml
    Note over FS: App service + optional<br/>Redis (cache/tasks)<br/>PostgreSQL (database)<br/>Nginx (reverse proxy)

    CLI->>Gen: Generate Kubernetes manifests
    Gen->>FS: k8s/deployment.yaml
    Gen->>FS: k8s/service.yaml
    Gen->>FS: k8s/ingress.yaml
    Gen->>FS: k8s/configmap.yaml
    Gen->>FS: k8s/hpa.yaml

    CLI->>Gen: Generate Nginx config
    Gen->>FS: nginx/nginx.conf
    Note over FS: Reverse proxy with<br/>static file serving<br/>WebSocket upgrade<br/>SSL termination config

    CLI->>Gen: Generate CI/CD pipeline
    Gen->>FS: .github/workflows/deploy.yml
    Note over FS: GitHub Actions workflow<br/>with lint → test → build → deploy

    CLI->>Gen: Generate monitoring config
    Gen->>FS: monitoring/prometheus.yml
    Gen->>FS: monitoring/grafana/dashboards/
    Note over FS: Prometheus scrape config<br/>+ Grafana dashboards

    CLI->>Gen: Generate .env.example
    Gen->>FS: .env.example

    CLI->>Gen: Generate Makefile
    Gen->>FS: Makefile
    Note over FS: dev, build, test,<br/>deploy, logs, shell targets

    Note over Dev,Registry: Docker Build Flow
    Dev->>CLI: aq deploy dockerfile
    CLI->>CLI: Build Docker image
    CLI->>Registry: docker push myapp:latest

    Note over Dev,Render: Render Cloud Deployment
    Dev->>CLI: aq deploy render
    CLI->>Render: Authenticate (API key from credential store)
    Render-->>CLI: Auth OK
    CLI->>Render: Create/update web service
    Note over Render: Configure:<br/>- Dockerfile path<br/>- Environment variables<br/>- Health check path<br/>- Port (8000)
    Render-->>CLI: Service URL

    Note over Dev,K8s: Kubernetes Deployment
    Dev->>CLI: aq deploy kubernetes
    CLI->>K8s: kubectl apply -f k8s/
    K8s->>K8s: Create Deployment (replicas: 3)
    K8s->>K8s: Create Service (ClusterIP)
    K8s->>K8s: Create Ingress (TLS)
    K8s->>K8s: Create HPA (CPU > 70%)
    K8s-->>CLI: Resources applied

    Note over Dev,Monitor: Monitoring Setup
    Dev->>CLI: aq deploy monitoring
    CLI->>K8s: kubectl apply -f monitoring/
    K8s->>Monitor: Deploy Prometheus + Grafana
    Monitor-->>CLI: Dashboard URLs

    Note over Dev,Monitor: Running in Production
    Monitor->>K8s: Scrape /_health on each pod
    K8s-->>Monitor: Engine metrics + subsystem status
    Monitor->>Monitor: Alert if degraded
```

### Generated Dockerfile

```dockerfile
# Multi-stage build generated by aq deploy dockerfile
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV AQUILIA_WORKSPACE=/app
ENV AQUILIA_ENV=prod
EXPOSE 8000
CMD ["uvicorn", "aquilia.entrypoint:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Generated docker-compose.yml

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AQUILIA_WORKSPACE=/app
      - AQUILIA_ENV=prod
      - AQ_SECRET_KEY=${AQ_SECRET_KEY}
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/_health"]
      interval: 30s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Environment Configuration Tiers

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | `.env` file (loaded by `ConfigLoader`) | `SECRET_KEY=xxx` |
| 2 | Environment variables | `AQ_SECRET_KEY=xxx` |
| 3 | `workspace.py` config | `Integration.cache(backend="redis")` |
| 4 | Module defaults | `AppManifest.defaults` |
| 5 (lowest) | Framework defaults | `mode="prod"` |

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install ruff
      - run: ruff check aquilia/
      - run: ruff format --check aquilia/

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: ${{ matrix.python-version }} }
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short -q

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp:${{ github.sha }} .
      - run: docker push myapp:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install aquilia
      - run: aq deploy render
```