# Bug Fixes — Aquilia v1.3.3

Two genuine bugs in the ORM layer were discovered and fixed during a
production-grade audit of `aquilia/models`. Both were confirmed from source
code, reproduced in tests, and fixed with minimal, surgical changes.

---

## Fix 1 — `UUIDField(auto=True)` NULL Primary Key Insert

### Symptom

```python
class MyModel(Model):
    id = UUIDField(primary_key=True, auto=True)

instance = await MyModel.create(name="test")
print(instance.id)  # None  ← bug
```

Rows were inserted with `id = NULL` despite `auto=True` being set.

### Root Cause

`UUIDField.__init__` builds a `kwargs` dict that always pre-populates
`kwargs["default"] = default` (where `default = UNSET` when the caller didn't
pass one):

```python
# Before fix — BROKEN
kwargs = {
    ...
    "default": default,   # always present, even when default=UNSET
    ...
}
if auto:
    kwargs.setdefault("default", uuid.uuid4)  # no-op: key already exists
```

`dict.setdefault()` only acts when the key is **absent**. Since `"default"`
was always pre-populated, the `uuid.uuid4` callable was never stored.
`Field.has_default()` returned `False`, `get_default()` returned `None`, and
the `INSERT` wrote `NULL` into the primary key column.

### Fix

Replace the `setdefault` call with an explicit sentinel check:

```python
# After fix — CORRECT
if auto and default is UNSET:
    kwargs["default"] = uuid.uuid4
```

**File:** `aquilia/models/fields_module.py`

### Regression Tests — `tests/test_uuid_pk_auto.py` (34 tests)

| Group | Coverage |
|---|---|
| `TestUUIDFieldInit` | `auto=True` sets callable default, explicit default honored, `auto=False` no default |
| `TestUUIDFieldValidation` | UUID object, string, invalid string, None (nullable), empty string, wrong type |
| `TestUUIDFieldSerialisation` | `to_python` / `to_db` round-trip for all backends |
| `TestUUIDFieldSQLType` | `VARCHAR(36)` for SQLite/MySQL/Oracle, `UUID` for PostgreSQL |
| `TestUUIDFieldDeconstruct` | `deconstruct()` includes field type |
| `TestUUIDPkCreate` | `create()` sets UUID, two creates have distinct UUIDs, fetch by PK |
| `TestUUIDPkRoundtrip` | `from_row()` deserialises, `filter(pk=uuid)` works |
| `TestUUIDForeignKey` | FK child referencing UUID PK, multiple children same parent |

---

## Fix 2 — Transaction Nesting Depth Tracker

### Symptom

Under concurrent workloads or after task recycling by asyncio, the transaction
nesting depth could be:

- **Stale from a previous task**: new task inherits `depth > 0`, so
  `Atomic.__aenter__` creates a `SAVEPOINT` instead of issuing `BEGIN`. No
  real transaction is ever opened. Rollbacks silently do nothing.
- **Never cleaned up**: `_task_depths` accumulated integer keys from dead
  tasks, causing unbounded memory growth under high request concurrency.

### Root Cause

The original implementation:

```python
_task_depths: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

def _get_depth_holder() -> _DepthHolder:
    task_id = id(task)                    # id() of the current asyncio Task
    holder = _task_depths.get(task_id)
    if holder is None:
        holder = _DepthHolder(0)
        _task_depths[task_id] = holder    # stored by integer key, not weakly
    return holder
```

Three bugs in one:

1. **Memory leak**: `WeakValueDictionary` holds *values* weakly — the integer
   `id(task)` keys are strong references that are never freed. One entry per
   task, forever.

2. **`id()` reuse contamination**: CPython recycles memory addresses. A new
   asyncio task may receive the same `id()` as a previously-GC'd task. If the
   stale `_DepthHolder` for that address still exists, the new task finds it
   and inherits the wrong depth. Depending on the stale value:
   - `depth > 0` on first enter → savepoint instead of `BEGIN`
   - `depth > 0` left over after exit → every subsequent enter is treated as
     nested, no top-level transactions ever open again

3. **Architecture inconsistency**: Every other Aquilia subsystem (controller,
   auth, DI, DB engine, inspector, i18n) uses `ContextVar` for task-local
   state. `WeakValueDictionary + id(task)` was the single outlier.

### Fix

Replace the entire `_task_depths` / `_DepthHolder` / `_get_depth_holder`
infrastructure with a single `ContextVar[int]`:

```python
# After fix
import contextvars

_txn_depth: contextvars.ContextVar[int] = contextvars.ContextVar(
    "aquilia_txn_depth", default=0
)
```

In `Atomic.__aenter__`:

```python
depth = _txn_depth.get()
# outermost → self._depth_token = _txn_depth.set(1)
# nested    → self._depth_token = _txn_depth.set(depth + 1)
```

In `Atomic.__aexit__`:

```python
if self._depth_token is not None:
    _txn_depth.reset(self._depth_token)  # restore to previous value
```

`reset(token)` (not `set(depth - 1)`) ensures that if `__aenter__` raises
before the token is stored, `__aexit__` is a safe no-op — no underflow.

**File:** `aquilia/models/transactions.py`

### Why ContextVar Is Correct

| Property | Old: WeakValueDict + id(task) | New: ContextVar[int] |
|---|---|---|
| Memory leak | Yes (integer keys never freed) | No (freed with task context) |
| `id()` reuse contamination | Yes | No (each task gets own copy) |
| Concurrency-safe | Unreliable | Yes (`set()` is local to current context) |
| Child task isolation | None | Yes (child inherits at-copy-time value, mutations independent) |
| Consistent with codebase | No | Yes |

### Regression Tests — `tests/test_txn_depth_contextvar.py` (19 tests)

| Group | Coverage |
|---|---|
| `TestContextVarUsed` | `_txn_depth` is a `ContextVar`, default is 0, no `WeakValueDictionary` exported |
| `TestDepthTracking` | 0 before enter, 1 inside outermost, 2 inside nested, restored after rollback, restored after nested rollback |
| `TestConcurrencyIsolation` | Two `gather()` tasks see independent depths, sibling tasks start at 0, `id()` reuse doesn't contaminate |
| `TestStress` | 50 concurrent tasks with nested atomics, no depth corruption |
| `TestAtomicBehaviourAfterFix` | Commit/rollback still work, savepoint still works, durable rejected when nested, decorator form, on-commit/rollback hooks |

---

## Fix 3 — `Controller.render()` / `TemplateEngine` Resolution Failure (Issue #59)

### Symptom

Calling `return await self.render("index.html")` inside a controller handler raised:

```
aquilia.response.TemplateRenderError: [TEMPLATE_RENDER_ERROR] No TemplateEngine available.
Ensure TemplateMiddleware is installed or pass engine parameter.
```

### Root Cause Analysis

Audit of the template resolution lifecycle revealed five interlocking root causes:

1. **Async Event Loop Bridge Collision**: `Response.render()` checked `hasattr(container, "resolve")` before `hasattr(container, "resolve_async")`. Because `Container` defines both, calling `container.resolve()` inside an active asyncio loop invoked `_sync_bridge.run_sync()`, throwing `RuntimeError: Cannot run sync resolution from inside a running event loop`. The surrounding `try...except Exception: pass` swallowed the exception, leaving `engine = None`.
2. **Missing `_integration_type` in Builder**: `TemplatesIntegration.builder()` returned a dictionary lacking `"_integration_type": "templates"`, causing builder integration definitions to bypass `Workspace.integrate()` type indexing.
3. **Template Engine Unstored in Request State**: `TemplateMiddleware` set template context helpers on `request.state`, but did not store `request.state["template_engine"]`.
4. **Auto-Discovery Timing**: `AquiliaServer` only enabled templates if `template_config["enabled"]` was `True` during `initialize()`, before app manifests were scanned.
5. **Search Path Resolution**: Relative search paths were resolved against `cwd` rather than `workspace_root`.

### Fix

- **`aquilia/response.py`**: Prioritized `hasattr(container, "resolve_async")` over `container.resolve()` when resolving dependencies inside async `Response.render()`.
- **`aquilia/integrations/templates.py`**: Set `"_integration_type": "templates"` in `TemplatesIntegration._Builder.__init__()`.
- **`aquilia/templates/middleware.py`**: Added `engine` parameter to `TemplateMiddleware` and stored `request.state["template_engine"] = self.engine`.
- **`aquilia/server.py`**: Auto-enabled template rendering whenever a `templates/` directory is detected in workspace root or modules, passed `engine=self.template_engine` to `TemplateMiddleware`, and resolved relative search paths against `workspace_root`.

### Verification — `tests/test_issue59_template_render.py`

| Test | Assertion | Status |
|---|---|---|
| `test_issue59_controller_render_resolution` | `await self.render(...)` resolves `TemplateEngine` & returns `200 OK` HTML | Passed |
