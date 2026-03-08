# Session Module — Modern Framework Comparison

## Comparison Matrix

### Aquilia vs Flask (flask-session / itsdangerous)

| Feature | Aquilia | Flask |
|---|---|---|
| Session ID Entropy | 256-bit CSPRNG | 128-bit (itsdangerous) |
| Server-side Storage | ✅ MemoryStore, FileStore | Via flask-session extension |
| Policy Objects | ✅ SessionPolicy dataclass | ❌ Config dict only |
| Idle Timeout | ✅ Native | ❌ Not built-in |
| Absolute Timeout | ✅ Native | ❌ Not built-in |
| ID Rotation on Auth | ✅ Automatic | ❌ Manual |
| Fingerprint Binding | ✅ IP + User-Agent | ❌ Not available |
| Concurrency Limits | ✅ Per-principal | ❌ Not available |
| Typed Faults | ✅ 16 fault types | ❌ Bare exceptions |
| Session Guards | ✅ Composable | ❌ Not available |
| Fluent Builders | ✅ SessionPolicyBuilder | ❌ Not available |
| Transport Agnostic | ✅ Cookie + Header | ❌ Cookie only |

### Aquilia vs Django

| Feature | Aquilia | Django |
|---|---|---|
| Session ID Entropy | 256-bit | 128-bit (hashlib) |
| Storage Backends | Memory, File | DB, Cache, File, Cookie |
| Policy System | ✅ Typed policies | ❌ Settings only |
| Idle Timeout | ✅ Per-policy | ✅ SESSION_COOKIE_AGE |
| Absolute Timeout | ✅ Per-policy | ❌ Not built-in |
| ID Rotation | ✅ Policy-driven | ✅ cycle_key() manual |
| Fingerprint Binding | ✅ Native | ❌ Not available |
| Concurrency Limits | ✅ Native | ❌ Not available |
| Async Support | ✅ Full async | ⚠️ Partial (Django 4.1+) |
| Typed State | ✅ SessionState class | ❌ Plain dict |
| DI Integration | ✅ Deep | ❌ None |

### Aquilia vs FastAPI (no built-in sessions)

| Feature | Aquilia | FastAPI |
|---|---|---|
| Built-in Sessions | ✅ Full module | ❌ None (use Starlette) |
| Session Management | ✅ Engine + policies | ❌ Requires 3rd party |
| Security Defaults | ✅ OWASP compliant | ❌ No defaults |
| Middleware | ✅ SessionMiddleware | ❌ Must build |
| DI for Sessions | ✅ Native | ❌ Manual Depends() |
| Decorators | ✅ @session, @authenticated | ❌ None |
| Guards | ✅ SessionGuard system | ❌ None |

### Aquilia vs Express.js (express-session)

| Feature | Aquilia | express-session |
|---|---|---|
| Session ID | 256-bit CSPRNG | 128-bit uid-safe |
| Typed Policies | ✅ SessionPolicy | ❌ Config object |
| Fingerprinting | ✅ Native | ❌ Not available |
| Concurrency | ✅ Per-principal | ❌ Not available |
| ID Rotation | ✅ Automatic | ✅ req.session.regenerate() |
| Async/Await | ✅ Native | ⚠️ Callback-based |
| Typed Faults | ✅ 16 types | ❌ Error strings |

### Aquilia vs Spring Session (Java)

| Feature | Aquilia | Spring Session |
|---|---|---|
| Storage | Memory, File | Redis, JDBC, Hazelcast |
| Concurrency | ✅ Policy-based | ✅ ConcurrentSessionFilter |
| Fingerprinting | ✅ Native | ❌ Manual |
| Policy System | ✅ Fluent builders | ⚠️ XML/annotation config |
| ID Rotation | ✅ Policy-driven | ✅ changeSessionId() |
| Transport | Cookie, Header | Cookie, Header |

## Unique Aquilia Advantages

1. **Policy-Driven Architecture**: No other framework offers typed `SessionPolicy`
   objects with fluent builders (`SessionPolicy.for_admin_users().build()`)

2. **Integrated Fault System**: 16 typed fault classes vs bare exceptions in
   every other framework

3. **Fingerprint Binding**: Built-in OWASP hijack detection — no other Python
   framework offers this natively

4. **Session Guards**: Composable authorization guards with `@requires()` —
   similar to NestJS guards but for sessions specifically

5. **Typed Session State**: `SessionState` class with `Field` descriptors —
   type-safe session data access

6. **Transport Agnosticism**: First-class header-based sessions for APIs alongside
   cookie-based for web — unique among Python frameworks

7. **Concurrency Controls**: Per-principal session limits with eviction strategies
   — only Spring Session offers comparable functionality
