# Session Lifecycle Analysis

## 7-Phase Lifecycle

### Phase 1: Detection
**Location:** `SessionEngine.resolve()` → `transport.extract(request)`

The transport adapter extracts the session ID from the incoming request:
- **CookieTransport**: Parses `Cookie` header, finds `cookie_name`
- **HeaderTransport**: Reads custom header (e.g., `X-Session-ID`)

**Security:** Cookie parsing now hardened with length limits (16 KiB),
pair count limits (64), and character validation.

### Phase 2: Resolution
**Location:** `SessionEngine.resolve()` → `_load_existing()` / `_create_new()`

If a session ID is found:
1. Parse with `SessionID.from_string()` (validates format, length, encoding)
2. Load from store
3. If not found or invalid, create new

If no session ID found, create new session immediately.

**Security:** `SessionID.from_string()` now validates input length (128 max),
type, and raises `SessionInvalidFault` (not raw `ValueError`).

### Phase 3: Validation
**Location:** `SessionEngine._load_existing()` → `policy.is_valid()`

Three timeout checks:
1. **TTL Expiry**: `session.is_expired(now)` → `SessionExpiredFault`
2. **Idle Timeout**: `session.idle_duration(now) >= policy.idle_timeout` → `SessionIdleTimeoutFault`
3. **Absolute Timeout**: `session.age(now) >= policy.absolute_timeout` → `SessionAbsoluteTimeoutFault`

**Security:** All three timeouts use structured faults. Engine handles each
fault type explicitly for observability.

### Phase 4: Binding
**Location:** `SessionEngine._load_existing()` (fingerprint) + `SessionMiddleware.__call__()` (DI/state)

1. **Fingerprint verification** (if policy enables it):
   - Compute `SHA-256(IP|User-Agent)[:32]`
   - Compare with stored fingerprint using `secrets.compare_digest()`
   - On mismatch: **destroy session** + raise `SessionFingerprintMismatchFault`

2. **DI binding**:
   - `container.register_instance(Session, session, scope="request")`
   - `request.state["session"] = session`
   - `ctx.session = session`

3. **Session touch**:
   - `session.touch(now)` updates `last_accessed_at`

**Security:** Fingerprint mismatch now destroys the session in store (OWASP).

### Phase 5: Mutation
**Location:** Handler execution (user code)

The handler reads/writes session data:
- `session["key"] = value` (triggers `_DirtyTrackingDict`)
- `session.data["key"] = value` (also tracked)
- `session.mark_authenticated(principal)` (sets flags + marks dirty)

**Security:** Read-only sessions raise `SessionLockedFault`. Data key count
limited to `MAX_DATA_KEYS = 256`.

### Phase 6: Commit
**Location:** `SessionEngine.commit()`

1. **Rotation check**: If `policy.should_rotate(session, privilege_changed)`:
   - Create new `SessionID`
   - Copy data + metadata
   - Delete old session from store
   - Preserve fingerprint

2. **Concurrency check** (on privilege change + authenticated):
   - Count sessions for principal
   - Reject, evict oldest, or evict all based on policy

3. **Persist**: If `policy.should_persist(session) and session.is_dirty`:
   - `store.save(session)`
   - `session.mark_clean()`

**Security:** Concurrency checked BEFORE save (prevents race condition).

### Phase 7: Emission
**Location:** `SessionEngine.commit()` → `transport.inject(response, session)`

Transport writes session reference to response:
- **CookieTransport**: `response.set_cookie(name, value, max_age, secure, httponly, samesite)`
- **HeaderTransport**: `response.headers[header_name] = session_id`

**Security:** Cookie flags (Secure, HttpOnly, SameSite) enforced by policy.

## Lifecycle State Diagram

```
                  ┌──────────┐
                  │  No ID   │
                  └────┬─────┘
                       │ create_new()
                       ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Expired  │◄───│  Valid   │───►│ Invalid  │
│ (destroy)│    │ Session  │    │ (reject) │
└──────────┘    └────┬─────┘    └──────────┘
                     │
              ┌──────┼──────┐
              ▼      ▼      ▼
         ┌────────┐ ┌────┐ ┌──────────┐
         │Mutated │ │Read│ │Privilege │
         │(dirty) │ │Only│ │ Change   │
         └───┬────┘ └────┘ └────┬─────┘
             │                   │
             ▼                   ▼
         ┌────────┐         ┌────────┐
         │Persist │         │Rotate  │
         │(save)  │         │(new ID)│
         └───┬────┘         └───┬────┘
             │                   │
             └───────┬───────────┘
                     ▼
              ┌──────────┐
              │  Emit    │
              │(response)│
              └──────────┘
```
