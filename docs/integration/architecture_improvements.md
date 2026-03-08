# Architecture Improvements

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. Current Architecture Strengths

### 1.1 Manifest-First Design
The static validation phase (Aquilary) catches configuration errors before
any runtime code executes. Registry fingerprinting enables deployment gating.

### 1.2 Scope-Isolated DI
Copy-on-write request containers are an excellent design — they avoid full
dict copies on every request while maintaining isolation.

### 1.3 Effect System
Typed effects with automatic acquire/release are a significant differentiator.
The `@requires(DBTx['write'])` syntax is clean and expressive.

### 1.4 Fault-Centric Error Handling
Converting all errors to domain-specific Faults with structured metadata
enables better observability and error tracking.

### 1.5 Performance-Conscious Design
Object pooling (RequestCtx), cached middleware chains, O(1) static route
matching, and lock-free metrics demonstrate serious performance thought.

---

## 2. Recommended Improvements (Future)

### 2.1 Server.py Decomposition (Recommended Priority: Medium)

**Current State**: `server.py` is 3,391 lines handling:
- Middleware setup (600+ lines)
- Session engine creation (200+ lines)
- Auth manager creation (150+ lines)
- Admin wiring (500+ lines)
- MLOps wiring (200+ lines)
- Model registration (300+ lines)
- Controller loading (200+ lines)
- Static asset resolution (100+ lines)

**Recommendation**: Extract into focused modules:

```
aquilia/
  server.py              → Core orchestrator (~500 lines)
  subsystems/
    middleware_wiring.py  → Middleware setup + security
    session_wiring.py    → Session engine creation
    auth_wiring.py       → Auth manager creation
    admin_wiring.py      → Admin route registration
    model_wiring.py      → AMDL/Python model registration
    storage_wiring.py    → Storage backend initialization
```

Each module would expose a single function like:
```python
def wire_sessions(server: AquiliaServer, config: ConfigLoader) -> SessionEngine:
    ...
```

### 2.2 Middleware Priority Constants (Recommended Priority: Low)

**Current State**: Magic numbers scattered through `_setup_middleware()` and
`_setup_security_middleware()`.

**Recommendation**: Define a priority enum or constants module:

```python
class MiddlewarePriority:
    EXCEPTION = 1
    FAULT = 2
    PROXY_FIX = 3
    HTTPS_REDIRECT = 4
    REQUEST_SCOPE = 5
    STATIC = 6
    SECURITY_HEADERS = 7
    HSTS = 8
    CSP = 9
    REQUEST_ID = 10
    CORS = 11
    RATE_LIMIT = 12
    SESSION_AUTH = 15
    CSRF = 20
    I18N = 24
    TEMPLATES = 25
    CACHE = 26
    USER = 50
```

### 2.3 Subsystem Interface Protocol (Recommended Priority: Low)

**Current State**: Each subsystem (mail, cache, storage, i18n, tasks) has
a slightly different initialization pattern in server.py.

**Recommendation**: Define a `Subsystem` protocol:

```python
class Subsystem(Protocol):
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    def register_in_container(self, container: Container) -> None: ...
```

This would standardize the `_setup_*()` / `startup()` / `shutdown()` pattern
and reduce boilerplate in `server.py`.

### 2.4 Config Access Typing (Recommended Priority: Low)

**Current State**: Config access uses string keys with dict-like access:
```python
session_config = self.config.get_session_config()
auth_config = self.config.get_auth_config()
```

Some methods also use dot-notation strings:
```python
self.config.get("server.debug", False)
self.config.get("database.url", None)
```

**Recommendation**: Consider typed config sections to leverage IDE support:
```python
@dataclass
class SecurityConfig:
    cors_enabled: bool = False
    csrf_protection: bool = False
    ...

config.security  # typed access
```

---

## 3. Architecture Consistency Assessment

### 3.1 Consistent Patterns ✅

| Pattern | Usage | Consistency |
|---------|-------|-------------|
| DI registration | `ValueProvider` in all containers | ✅ Consistent |
| Fault handling | Domain-specific Fault subclasses | ✅ Consistent |
| Async lifecycle | `initialize()` / `shutdown()` | ✅ Mostly consistent |
| Config reading | `self.config.get_*_config()` | ✅ Consistent |
| Middleware registration | `middleware_stack.add(mw, priority=N)` | ✅ Consistent |
| Logging | `self.logger.info/error/debug()` | ✅ Consistent |

### 3.2 Minor Inconsistencies

| Inconsistency | Where | Impact |
|---------------|-------|--------|
| `hasattr` checks for subsystems | `server.py` startup/shutdown | Low — defensive but verbose |
| String tokens for auth sub-components | `server.py:310-314` | Low — works but less type-safe |
| Mixed `_setup_*` and inline in `_setup_middleware` | Session/auth setup | Low — could be extracted |

---

## 4. No Breaking Changes Recommended

The current architecture is sound and all 4,702 tests pass. The improvements
above are non-urgent refactoring opportunities that would improve maintainability
without changing behavior. The two integration fixes (INT-01, INT-02) are
backward-compatible and risk-free.
