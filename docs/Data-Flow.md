# Aquilia — Data Flow

> Complete request lifecycle, internal service flow, background job flow, and database interaction patterns.

---

## 1. HTTP Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant U as Uvicorn
    participant A as ASGIAdapter
    participant MW as MiddlewareStack
    participant R as ControllerRouter
    participant E as ControllerExecutor
    participant H as Handler
    participant DB as Database

    C->>U: HTTP Request
    U->>A: ASGI scope, receive, send
    A->>A: Check /_health (bypass)
    A->>A: Create RequestContext (UUID)
    A->>A: Build Request object
    A->>MW: Execute middleware chain
    
    Note over MW: 1. ProxyFix (trusted proxy)<br/>2. HTTPS Redirect<br/>3. Static Files<br/>4. Security Headers<br/>5. HSTS<br/>6. CSP (nonce)<br/>7. CSRF<br/>8. CORS<br/>9. Rate Limiting<br/>10. Request ID<br/>11. Timing<br/>12. Timeout<br/>13. Gzip<br/>14. Session<br/>15. Auth<br/>16. DI Container
    
    MW->>R: Route matching
    R->>R: Tier 1: O(1) static lookup
    R->>R: Tier 2: O(k) dynamic regex
    R->>E: CompiledRoute + match params
    
    E->>E: Create DI request container
    E->>E: Execute FlowPipeline guards
    E->>E: Evaluate Clearance
    E->>E: Run Interceptors (before)
    E->>E: Bind parameters (path/query/body/DI)
    E->>E: Validate Blueprint (cast → seal)
    E->>H: Call handler method
    H->>DB: ORM query
    DB-->>H: Results
    H-->>E: Response data
    E->>E: Run Interceptors (after)
    E->>E: Content negotiation
    E->>E: Pagination
    E->>E: Blueprint mold (serialize)
    E-->>MW: Response object
    MW-->>A: Response with headers
    A-->>U: ASGI send
    U-->>C: HTTP Response
```

### Detailed Phase Breakdown

#### Phase 1: ASGI Reception
1. Uvicorn receives raw HTTP connection
2. `ASGIAdapter.__call__` invoked with `(scope, receive, send)`
3. Health check (`/_health`) served before middleware if path matches
4. `RequestContext` created with UUID, timestamps

#### Phase 2: Middleware Chain
Deterministic ordering: Global < App < Controller < Route, then by priority within each scope.

```
Request → ProxyFix → HTTPS → Static → Helmet → HSTS → CSP → CSRF → CORS → RateLimit → RequestID → Timing → Timeout → Gzip → Session → Auth → DI → [Next]
```

Each middleware can:
- Short-circuit with a response (e.g., rate limiter returns 429)
- Modify the request (e.g., ProxyFix rewrites client IP)
- Modify the response (e.g., CORS adds headers)
- Wrap execution (e.g., Timeout adds `asyncio.wait_for`)

#### Phase 3: Route Matching
1. Static routes checked via hash map → O(1)
2. Dynamic routes matched via specificity-sorted regex → O(k)
3. Path parameters extracted and type-cast
4. Query parameters validated

#### Phase 4: Controller Execution (12 sub-phases)

```mermaid
graph TD
    A[1. DI Container Creation] --> B[2. Flow Pipeline]
    B --> C[3. Clearance Evaluation]
    C --> D[4. Interceptors Before]
    D --> E[5. Parameter Binding]
    E --> F[6. Blueprint Validation]
    F --> G[7. Handler Execution]
    G --> H[8. Exception Filters]
    H --> I[9. Interceptors After]
    I --> J[10. Content Negotiation]
    J --> K[11. Pagination]
    K --> L[12. Response Building]
```

1. **DI Container**: Request-scoped container created as child of app container
2. **Flow Pipeline**: Guards evaluated in priority order → Transform → Effect acquisition
3. **Clearance**: Class + method-level clearance merged and evaluated (level/entitlements/conditions/compartments)
4. **Interceptors**: Before-hooks for cross-cutting concerns
5. **Parameter Binding**: Path params, query params, headers, body → handler arguments via type annotations
6. **Blueprint Validation**: If handler accepts a Blueprint type, request body is cast and sealed
7. **Handler**: User business logic executes
8. **Exception Filters**: Chain of Responsibility for handler errors
9. **Interceptors**: After-hooks
10. **Content Negotiation**: Accept header → renderer selection (JSON, HTML, XML, YAML, etc.)
11. **Pagination**: If QuerySet returned, paginate via configured strategy
12. **Response**: Blueprint mold (serialize), set headers, cookies, status code

---

## 2. Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Auth Middleware
    participant SM as Session Manager
    participant AM as AuthManager
    participant RL as RateLimiter
    participant IS as IdentityStore
    participant CS as CredentialStore
    participant TM as TokenManager
    participant MFA as MFAManager

    C->>MW: Request with credentials
    MW->>SM: Resolve session (cookie/header)
    
    alt Bearer Token Present
        MW->>TM: Validate token
        TM->>TM: Verify signature (RS256/ES256/EdDSA)
        TM->>TM: Check revocation
        TM-->>MW: Token claims
        MW->>IS: Load identity by ID
    else API Key Present
        MW->>AM: authenticate_api_key()
        AM->>RL: Check rate limit
        AM->>CS: Load API key by prefix
        AM->>AM: SHA-256 hash → constant-time compare
        AM->>AM: Check expiration, revocation, scopes
    else Password Auth (login endpoint)
        C->>AM: authenticate_password(username, password)
        AM->>RL: Check rate limit (sliding window)
        RL-->>AM: OK or RateLimitExceededFault
        AM->>IS: Find identity by username
        AM->>CS: Load password credential
        AM->>AM: Argon2id verify (or PBKDF2 fallback)
        AM->>AM: Rehash if algorithm upgraded
        
        alt MFA Enrolled
            AM->>MFA: Check verification required
            MFA-->>AM: MFA challenge
            AM-->>C: 401 MFA Required
            C->>AM: TOTP code / WebAuthn assertion
            AM->>MFA: Verify
        end
        
        AM->>TM: Issue access + refresh tokens
        AM->>SM: Create session
    end
    
    MW->>MW: Inject identity into DI container
    MW->>MW: Set request.identity
```

---

## 3. Database Interaction Flow

```mermaid
sequenceDiagram
    participant H as Handler
    participant M as Model
    participant QS as QuerySet
    participant SQL as SQLBuilder
    participant DB as Database
    participant A as Adapter
    participant Driver as DB Driver

    H->>M: Model.objects.filter(name="x")
    M->>QS: Create QuerySet clone
    QS->>QS: Store filter clause
    
    H->>QS: .select_related("author")
    QS->>QS: Add JOIN
    
    H->>QS: await .all()
    QS->>SQL: Build SELECT
    SQL->>SQL: Dialect-aware SQL generation
    SQL-->>QS: SQL string + params
    
    QS->>DB: execute(sql, params)
    DB->>A: adapter.fetch_all(sql, params)
    A->>A: adapt_placeholders (? → $1 / %s / :1)
    A->>Driver: asyncpg/aiosqlite/aiomysql/oracledb
    Driver-->>A: Raw rows
    A-->>DB: Dict rows
    DB-->>QS: Results
    QS->>M: Hydrate Model instances
    M-->>H: List[Model]
```

### Transaction Flow

```mermaid
sequenceDiagram
    participant H as Handler
    participant TX as Transaction
    participant DB as Database
    participant A as Adapter

    H->>TX: async with transaction():
    TX->>DB: begin_transaction()
    DB->>A: begin()
    A->>A: Acquire dedicated connection
    
    H->>DB: execute(INSERT ...)
    H->>DB: execute(UPDATE ...)
    
    alt Nested Transaction
        H->>TX: async with transaction():
        TX->>DB: create_savepoint("sp_1")
        DB->>A: savepoint("sp_1")
        H->>DB: execute(...)
        
        alt Success
            TX->>DB: release_savepoint("sp_1")
        else Error
            TX->>DB: rollback_to_savepoint("sp_1")
        end
    end
    
    alt Success
        TX->>DB: commit()
        TX->>TX: Fire on_commit hooks
    else Error
        TX->>DB: rollback()
        TX->>TX: Fire on_rollback hooks
    end
    
    A->>A: Release connection to pool
```

---

## 4. Background Job Flow

```mermaid
sequenceDiagram
    participant H as Handler
    participant TM as TaskManager
    participant Q as Queue (Priority)
    participant W as Worker
    participant DLQ as Dead Letter Queue

    H->>TM: my_task.delay(arg1, arg2)
    TM->>TM: Create TaskResult (PENDING)
    TM->>Q: Enqueue with priority
    
    loop Worker Loop
        W->>Q: Dequeue highest priority job
        Q-->>W: TaskResult
        W->>W: Update state → RUNNING
        W->>W: Execute task function
        
        alt Success
            W->>W: State → COMPLETED
            W->>TM: Fire on_complete callbacks
        else Failure
            W->>W: Increment attempt count
            
            alt Can Retry
                W->>W: Calculate backoff delay
                W->>Q: Re-enqueue with delay
            else Max Retries Exceeded
                W->>W: State → DEAD_LETTER
                W->>DLQ: Move to dead letter
                W->>TM: Fire on_dead_letter callbacks
            end
        end
    end
    
    loop Scheduler Loop
        TM->>TM: Check periodic tasks
        TM->>TM: Evaluate cron/interval schedules
        TM->>Q: Enqueue due tasks
    end
    
    loop Cleanup Loop
        TM->>TM: Remove completed jobs > retention
        TM->>TM: Remove expired dead letters
    end
```

---

## 5. Effect System Flow

```mermaid
sequenceDiagram
    participant E as ControllerExecutor
    participant FP as FlowPipeline
    participant ER as EffectRegistry
    participant EP as EffectProvider
    participant H as Handler

    E->>FP: Execute pipeline
    FP->>FP: Collect effect requirements (from decorators)
    FP->>FP: Topological sort by dependencies
    
    loop For each required effect
        FP->>ER: Get provider for effect token
        ER-->>FP: EffectProvider
        FP->>EP: acquire() — per-request
        EP-->>FP: Effect handle (DB conn, cache namespace, etc.)
    end
    
    FP->>FP: Inject effects into FlowContext
    FP->>H: Call handler with injected effects
    H-->>FP: Result
    
    loop Release in reverse order
        FP->>EP: release()
    end
```

---

## 6. Admin Panel Flow

```mermaid
graph TD
    A[Browser] --> B[/admin/ routes]
    B --> C{Session Auth}
    C -->|No session| D[Login Page]
    C -->|Valid session| E[Permission Check]
    E -->|Denied| F[403 Forbidden]
    E -->|Allowed| G[Admin Controller]
    
    G --> H[Dashboard]
    G --> I[Model CRUD]
    G --> J[Audit Log]
    G --> K[Monitoring]
    G --> L[Query Inspector]
    G --> M[Error Tracker]
    
    I --> N[ModelAdmin Options]
    N --> O[List View]
    N --> P[Detail View]
    N --> Q[Create/Edit Form]
    N --> R[Delete Confirmation]
    
    O --> S[Filters + Search + Pagination]
    Q --> T[Validation + Hooks + Signals]
    T --> U[Audit Entry]
```

---

## 7. ML Inference Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as MLOps Controller
    participant RT as TrafficRouter
    participant ABQ as AdaptiveBatchQueue
    participant IP as InferencePipeline
    participant R as Runtime
    participant M as LoadedModel

    C->>API: POST /api/v1/models/{name}/predict
    API->>RT: Route request (canary/A-B)
    RT->>RT: Select model version (weighted)
    RT-->>API: Model version + config
    
    API->>ABQ: Enqueue request
    ABQ->>ABQ: Wait for batch fill or timeout
    ABQ->>ABQ: Adapt batch size (self-tuning)
    ABQ-->>IP: Batch of requests
    
    IP->>IP: Preprocess hooks
    IP->>R: Batch inference
    R->>M: ensure_loaded() (LRU cache)
    M-->>R: Model weights
    R->>R: Run prediction
    R-->>IP: Raw outputs
    IP->>IP: Postprocess hooks
    IP-->>API: Results
    
    API->>API: Record metrics (latency, throughput)
    API->>API: Record for drift detection
    API-->>C: JSON response
```

---

## 8. Build & Deploy Flow

```mermaid
graph TD
    A[aq build] --> B[Phase 1: Validate]
    B --> C[Phase 2: Discover]
    C --> D[Phase 3: Compile]
    D --> E[Phase 4: Bundle]
    E --> F[Phase 5: Finalize]
    
    B --> B1[Workspace.py syntax check]
    B --> B2[Manifest structure validation]
    B --> B3[Import path verification]
    
    C --> C1[AST-based class scanning]
    C --> C2[Controller/Service/Model detection]
    C --> C3[Manifest synchronization]
    
    D --> D1[Route compilation]
    D --> D2[DI graph building]
    D --> D3[Artifact generation]
    
    E --> E1[CROUS binary encoding]
    E --> E2[SHA-256 digest computation]
    E --> E3[Bundle assembly]
    
    F --> F1[Build manifest generation]
    F --> F2[Fingerprint computation]
    F --> F3[Deploy context creation]
    
    F3 --> G{Deploy target}
    G --> H[Docker + docker-compose]
    G --> I[Kubernetes manifests]
    G --> J[CI/CD pipelines]
    G --> K[Nginx config]
    G --> L[Prometheus + Grafana]
```

---

## 9. WebSocket Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as ASGIAdapter
    participant R as SocketRuntime
    participant G as Guards
    participant SC as SocketController
    participant B as Backend (Redis/Memory)

    C->>A: WebSocket handshake
    A->>R: Route to socket controller
    R->>G: Evaluate connection guards
    
    alt Guard Denied
        R-->>C: Close (403)
    else Guard Passed
        R->>SC: @on_connect handler
        R->>B: Register connection
        
        loop Message Loop
            C->>R: Message (text/binary)
            R->>R: Decode envelope
            R->>SC: @on_message handler
            SC-->>R: Response
            R->>C: Send response
        end
        
        alt Broadcast
            SC->>B: Publish to channel
            B->>B: Fan-out to all subscribers
            B-->>C: Broadcast message
        end
        
        C->>R: Close
        R->>SC: @on_disconnect handler
        R->>B: Unregister connection
    end
```

---

## 10. Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: New request (no session cookie)
    Created --> Active: First write / explicit create
    Active --> Active: Read/Write operations
    Active --> Rotated: Privilege change detected
    Rotated --> Active: New session ID issued
    Active --> Extended: Idle timeout approaching
    Extended --> Active: TTL refreshed
    Active --> Expired: TTL exceeded
    Active --> Destroyed: Explicit logout / delete
    Expired --> [*]
    Destroyed --> [*]
    
    note right of Rotated
        Session rotation prevents
        session fixation attacks
    end note
    
    note right of Extended
        Sliding window renewal
        based on policy
    end note
```
