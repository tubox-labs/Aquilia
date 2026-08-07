# Migration Guide — 1.4.0b0 → 1.4.0b1

The transition to Aquilia v1.4.0b1 is largely transparent, as the focus was on replacing internal engines rather than shifting public API paradigms. However, a few structural and configuration changes require attention.

## 1. Dependency Injection Settings (`DISettings`)

To drastically reduce overhead during dependency resolution, properties on the `DISettings` configuration object have been flattened into standard slot fields.

**Breaking Change:** `_strict_scopes` is now public.
If you programmatically configure your DI container in `workspace.py` or during testing, you must update references.

**Before (v1.4.0b0):**
```python
from aquilia.di import Container

container = Container()
# Accessing private property
container.settings._strict_scopes = True
```

**After (v1.4.0b1):**
```python
from aquilia.di import Container

container = Container()
# It is now a strictly validated public slot field
container.settings.strict_scopes = True
```

**New Field:** `scope_check_enabled`. 
This field controls whether scope hierarchy rules are actively checked during resolution. It defaults to `True` but can be turned off in extreme high-throughput scenarios where you have guaranteed no scope violations via static analysis.

## 2. Unified JSON Codec (`aquilia.json`)

Aquilia no longer depends on `orjson` or `ujson` in its `pyproject.toml`. 

- **If you only used `orjson` because Aquilia required it:** You can safely remove it from your project dependencies. 
- **If you imported `orjson` directly in your own code:** You should migrate to the new `aquilia.json` unified codec to maintain maximum performance.

**Migration Example:**
```python
# OLD
import orjson
data = orjson.loads(payload)
byte_string = orjson.dumps(obj)

# NEW
import aquilia.json
data = aquilia.json.loads(payload)
byte_string = aquilia.json.dumps(obj)
```
`aquilia.json` automatically uses the ultra-fast C++ `yyjson` backend when available, and falls back to the Python standard library if not.

## 3. `validate_body` Optimizations

The `@validate_body` decorator no longer triggers the controller to double-bind the payload. 
- **User Action:** None required.
- **Impact:** You will notice a dramatic drop in CPU usage on write-heavy endpoints. If you had custom middleware inspecting `request.body` after validation, be aware that the body is now parsed exactly once and stored in `request.validated_data`.

## 4. SQLite Inline Queries

By default, Aquilia now executes fast database queries inline on the asyncio event loop.
- **Configuration:** The new setting `inline_fast_queries` defaults to `True`.
- **Threshold:** `inline_max_duration_ms` defaults to `5.0`.
- **Action:** If you heavily abuse your SQLite database with long table scans that cannot be indexed, you *might* see event loop stalls before the engine demotes the query. If you prefer the old (but slower) guaranteed thread-pool behavior, disable it in your database configuration:

```python
# workspace.py
from aquilia.pyconfig import AquilaConfig

class Database(AquilaConfig.Database):
    inline_fast_queries = False
```

## 5. Native Extensions Optionality

The framework now distributes three C++ extensions (`_core`, `_dataengine`, `_json`). 

**How to Verify Native is Active:**
Run the following in your Aquilia environment:
```python
import aquilia.engines
print("Core:", aquilia.engines.engine_info())
print("Data:", aquilia.engines.dataengine_info())
import aquilia.json
print("JSON:", aquilia.json.backend())
```
If you see `"backend": "native"` or `"yyjson"`, the C++ accelerators are functioning.

**How to Disable:**
If you encounter segfaults or compilation errors on a highly esoteric architecture, you can force the Python fallback:
```bash
export AQUILIA_ENGINE=0
export AQUILIA_DATAENGINE=0
export AQUILIA_JSON_BACKEND=python
```

## Compatibility Matrix

| Component | Minimum Supported Version | Recommended |
|-----------|---------------------------|-------------|
| **Python**| 3.10 | 3.12+ |
| **OS** | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 13 |
| **SQLite**| 3.35.0 (for RETURNING) | 3.42.0+ |

## Upgrade Checklist

- [ ] Update `aquilia` in your `requirements.txt` or `pyproject.toml` to `1.4.0b1`.
- [ ] Remove `orjson` / `ujson` from your dependencies unless used extensively elsewhere.
- [ ] Search codebase for `_strict_scopes` and replace with `strict_scopes`.
- [ ] Replace direct imports of `json` or `orjson` with `aquilia.json`.
- [ ] Run your test suite. Monitor for any newly identified SQLite inline demotions in the logs (marked as `WARNING: Inline SQL demotion`).
