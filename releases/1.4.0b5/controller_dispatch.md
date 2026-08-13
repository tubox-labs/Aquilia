# Controller Dispatch Correctness — v1.4.0b5

## Previous API

Public controller declarations already allowed both forms:

```python
@GET("/sync")
def sync_handler(self, ctx):
    return {"ok": True}

@GET("/async")
async def async_handler(self, ctx):
    return {"ok": True}
```

The public API has not changed. The internal dispatch implementation was incorrect.

## Root Cause

`ControllerEngine._safe_call()` cached `inspect.iscoroutinefunction(func)` using `id(func)`. Accessing a bound method creates a temporary method object. Once released, CPython may reuse that memory address for another bound method. A synchronous method could therefore inherit an earlier asynchronous cache entry and the engine would execute:

```python
await sync_handler(...)
```

When the handler returned a dictionary, the request failed with `TypeError: 'dict' object can't be awaited`.

## New Behavior

The engine now calls the handler exactly once:

```python
result = func(*args, **kwargs)
if inspect.isawaitable(result):
    return await result
return result
```

This result-based rule supports:

- native `async def` handlers;
- synchronous handlers;
- callable objects;
- synchronous decorator wrappers that return a coroutine or other awaitable.

## Why It Is Better

- No unstable identity cache.
- No double invocation or side-effect duplication.
- The actual return value determines whether awaiting is necessary.
- Decorators do not need to preserve `inspect.iscoroutinefunction()` metadata to remain correct.

## Migration Guide

No application code change is required. Remove workarounds that converted every handler to `async def` solely to avoid intermittent dispatch failures.

Decorator authors should still use `functools.wraps()` for metadata and introspection quality, but correctness no longer depends on coroutine-function classification.

## Edge Cases

- A synchronous handler returning an awaitable is awaited.
- A synchronous handler returning a custom object implementing `__await__` is awaited.
- A handler returning an async iterator is not automatically consumed; async iterators are not awaitables and must be adapted to the framework's streaming response API.
- Returning a coroutine accidentally will execute it. Use type checking and tests to catch unintended coroutine returns.

## Performance

The removed dictionary cache is replaced by one constant-time `inspect.isawaitable()` call on the result. Handler invocation, DI, validation, and response conversion dominate this cost. The implementation prioritizes deterministic correctness.

## Testing Pattern

```python
async def test_mixed_handlers(engine):
    class Handler:
        async def asynchronous(self):
            return "async"

        def synchronous(self):
            return {"kind": "sync"}

    handler = Handler()
    assert await engine._safe_call(handler.asynchronous) == "async"
    assert await engine._safe_call(handler.synchronous) == {"kind": "sync"}
```

See the aqdocx [ControllerEngine guide](/docs/controllers/engine).
