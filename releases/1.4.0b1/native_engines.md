# Native Engines — v1.4.0b1

Aquilia v1.4.0b1 introduces three native C++ extensions to accelerate the most performance-critical paths of the framework. These extensions are built using `nanobind` and `scikit-build-core`, ensuring tight integration with Python while delivering C++ level performance and memory safety.

## The Three Extensions

The architectural strategy of v1.4.0b1 was to selectively rewrite pure Python bottlenecks in modern C++17, exposed via `nanobind`.

### 1. `aquilia/_core`
This extension houses fundamental framework primitives and shared state objects.
- **String Interner (`aquilia/_core/src/interner.cpp`)**: A high-performance string intern pool. It avoids redundant allocation of common HTTP headers, routing keys, and internal state strings. It is backed by a standalone C++ unit-test harness to verify concurrent safety.
- **Radix-Trie Router (`aquilia/_core/src/router.cpp`)**: Replaces the Python regex-based route matcher. The C++ radix trie efficiently maps URL paths to endpoint handlers and natively evaluates HTTP method eligibility, avoiding expensive Python function calls during route resolution.
- **RequestContext**: A native implementation with fixed slots. It replaces the old `RequestCtx` Python object pool (which profiling proved was net-negative for performance due to object lifecycle overhead and GC pressure).

### 2. `aquilia/_dataengine`
Dedicated to data parsing, runtime contract validation, and database hydration.
- **UUID Parser (`aquilia/_dataengine/src/uuid_parse.cpp`)**: A highly optimized parser for RFC 4122 UUIDs, bypassing the overhead of Python's `uuid.UUID` instantiation in hot paths.
- **FieldPlan Engine (`aquilia/_dataengine/src/fieldplan.cpp`)**: The core of the new validation architecture. It evaluates contract fields natively, applying type coercions and constraints at C-speed. (See [Validation Engine](validation_engine.md) for deeper details).
- **RowPlan Engine (`aquilia/_dataengine/src/rowplan.cpp`)**: Hydrates raw SQLite rows into mapped ORM objects efficiently, mapping database columns directly to native Python types without intermediate dictionary allocation.

### 3. `aquilia/_json`
A dedicated high-performance JSON engine backed by vendored `yyjson 0.10.0` (MIT license).
- Completely eliminates the framework's dependency on `orjson` or `ujson`.
- Uses advanced techniques like SWAR, direct heap-based emission, and arena parsing.
- (See [JSON Engine](json_engine.md) for exhaustive details).

---

## Build System Architecture

The build pipeline has transitioned to `scikit-build-core` for robust cross-platform C++ compilation.

### CMake Structure
The root `CMakeLists.txt` orchestrates the build, dynamically loading `nanobind` and locating Python development headers. 

```cmake
cmake_minimum_required(VERSION 3.15...3.27)
project(aquilia_engines LANGUAGES CXX)

find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(nanobind CONFIG REQUIRED)

# Add subdirectories for each extension
add_subdirectory(src/core)
add_subdirectory(src/dataengine)
add_subdirectory(src/json)
```

Each extension has its own `CMakeLists.txt` that defines the `nanobind_add_module` target, specifying compile options (like `-O3`, `-flto`, and MSVC `/O2`), and linking necessary internal headers.

---

## Fail-Soft Loading Pattern

A fundamental design invariant in Aquilia is that **native extensions are strictly optional**. The framework must run correctly on pure Python if the extensions are uncompilable, missing, or explicitly disabled.

This is achieved via the **Extension Loader Pattern**. Every native module is paired with a Python loader module (e.g., `aquilia/_dataengine_loader.py`).

### Loader Example

```python
# aquilia/_dataengine_loader.py

import os
import logging
import warnings

logger = logging.getLogger("aquilia.engines")

# Optionality flag check
_OPTIONAL = os.environ.get("AQUILIA_ENGINE_OPTIONAL", "OFF").upper() == "ON"
_DATAENGINE_ENABLED = os.environ.get("AQUILIA_DATAENGINE", "1") == "1"

_HAS_NATIVE = False

if _DATAENGINE_ENABLED:
    try:
        # Attempt to import the compiled C++ extension
        from aquilia._dataengine import (
            parse_uuid,
            FieldPlan,
            RowPlan,
            dataengine_info
        )
        _HAS_NATIVE = True
    except ImportError as e:
        if not _OPTIONAL:
            # If not marked optional, failure is fatal.
            raise RuntimeError(f"Failed to load required native _dataengine: {e}") from e
        
        logger.debug(f"Native _dataengine unavailable, falling back to pure Python: {e}")

if not _HAS_NATIVE:
    # Pure Python fallbacks
    from aquilia._fallback.dataengine import (
        parse_uuid,
        FieldPlan,
        RowPlan
    )
    def dataengine_info():
        return {"backend": "python", "version": "1.4.0"}
```

### CI Gates and Testing
To guarantee the fail-soft mechanism works, CI runs the entire test suite in two modes:
1. **Native Mode**: Wheels are compiled, all extensions are loaded.
2. **Fallback Mode**: `AQUILIA_ENGINE_OPTIONAL=ON` is set, C++ extensions are explicitly deleted from the build environment, and the suite runs purely on Python.

All 123 Python tests, plus 104 differential fuzzing tests, must pass in both configurations. Furthermore, 32 C++ specific tests run under ASAN (AddressSanitizer), UBSAN (UndefinedBehaviorSanitizer), and TSAN (ThreadSanitizer) to ensure memory safety.

---

## Environment Variable Reference

The extensions can be controlled via environment variables during both build time (via `pip`) and runtime:

| Variable | Values | Effect |
|---|---|---|
| `AQUILIA_ENGINE_OPTIONAL` | `ON` / `OFF` | **Build:** If `ON`, compilation failures are ignored. **Runtime:** If `ON`, `ImportError` on extensions logs a debug message and uses python fallbacks instead of crashing. (Default: `OFF`) |
| `AQUILIA_ENGINE` | `1` / `0` | If `0`, disables the `_core` native extension at runtime, forcing pure Python routing and request context. |
| `AQUILIA_DATAENGINE` | `1` / `0` | If `0`, disables the `_dataengine` native extension, forcing pure Python validation and hydration. |
| `AQUILIA_JSON_BACKEND` | `native` / `python` | Explicitly overrides the JSON backend used by `aquilia.json`. |

### Introspection APIs

You can programmatically verify which engines are active at runtime using the introspection functions provided by the loaders:

```python
import aquilia.engines

print(aquilia.engines.engine_info())
# {'backend': 'native', 'router': 'radix', 'version': '1.4.0'}

print(aquilia.engines.dataengine_info())
# {'backend': 'native', 'uuid': 'c++', 'fieldplan': 'c++'}
```
