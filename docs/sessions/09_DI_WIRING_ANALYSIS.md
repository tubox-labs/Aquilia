# Session DI Wiring Analysis

## Integration Points

### 1. Server-Level Engine Creation (`aquilia/server.py`)

The server creates the `SessionEngine` during app initialization:

```python
_resolve_store_from_name(name, config)    # "memory" → MemoryStore, "file" → FileStore
_resolve_transport_from_policy(policy)     # "cookie" → CookieTransport, "header" → HeaderTransport
_create_session_engine(session_config)     # 3 config formats supported
```

Three config formats:
1. **Integration config** — From workspace integration module
2. **Workspace config** — From `workspace.py` settings
3. **Dict config** — Raw dictionary configuration

### 2. Middleware Registration

`SessionMiddleware` is registered in the middleware stack (priority ~15):
- Resolves session at request start
- Registers session in DI container as request-scoped instance
- Stores session in `request.state["session"]`
- Commits session at request end

### 3. DI Container Registration

```python
# In SessionMiddleware.__call__()
from aquilia.sessions import Session
await container.register_instance(Session, session, scope="request")
```

This allows controllers to receive `Session` via dependency injection:
```python
async def handler(session: Session):
    user = session.principal
```

### 4. RequestCtx Binding

```python
if hasattr(ctx, 'session'):
    ctx.session = session
```

Controllers can also access sessions via `ctx.session`.

### 5. Decorator Integration

Session decorators extract sessions from both `kwargs` and `RequestCtx`:

```python
def _extract_session(args, kwargs) -> Session | None:
    session = kwargs.get('session')
    if session is not None:
        return session
    for arg in args:
        if hasattr(arg, 'session') and hasattr(arg, 'request'):
            return arg.session
    return None
```

### 6. Guard Integration

Guards receive sessions and check authorization:
```python
class AdminGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return session.principal.get_attribute('role') == 'admin'
```

## Wiring Diagram

```
App Init:
  server.py → _create_session_engine() → SessionEngine
                                              ↓
                                    SessionMiddleware(engine)
                                              ↓
Request Flow:
  Request → SessionMiddleware
              ├── engine.resolve(request, container)
              ├── container.register_instance(Session, session)
              ├── request.state["session"] = session
              ├── ctx.session = session
              ├── next_handler(request, ctx)
              │     ↓
              │   Controller receives Session via:
              │     ├── DI injection (Session parameter)
              │     ├── ctx.session
              │     ├── request.state["session"]
              │     └── @session.require() decorator
              │
              └── engine.commit(session, response, privilege_changed)
```

## Security Assessment

| Wiring Point | Risk | Status |
|---|---|---|
| Engine creation | Store/transport misconfiguration | ✅ Validated factory methods |
| DI registration | Session scope leak | ✅ Request-scoped only |
| RequestCtx binding | Session accessible to all middleware | ✅ By design |
| Decorator extraction | Session from untrusted args | ✅ Type-checked |
| Guard checks | Bypass via direct handler call | ✅ Decorator-enforced |
| Middleware error handling | Session loss on exception | ✅ Graceful degradation |

## Conclusion

The session DI wiring is secure and well-integrated. Sessions flow through a
single controlled pipeline (middleware → DI → handler → commit) with no
shortcuts that bypass security checks.
