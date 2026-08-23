# Native C++ Acceleration Engines

Aquilia v1.4.0 introduces an optional high-performance C++20 acceleration layer built using `nanobind` and `scikit-build-core`. The native engines accelerate HTTP routing, request context management, ORM hydration, Contract validation, and JSON serialization with zero changes to user application code.

---

## The Three Extensions

### 1. `aquilia._core` — HTTP Radix-Trie Router & Request Context
* **Radix-Trie Router:** Implements a zero-copy C++ radix-trie matching algorithm for HTTP paths. Fallback per-method to pure Python occurs automatically when non-standard patterns are detected.
* **Fixed-Slot `RequestContext`:** Replaces dynamic Python `__dict__` allocations with 7 fixed C++ slots (`request`, `response`, `state`, `scope`, `container`, `identity`, `route`).
* **Custom GC Traversal (`tp_traverse` / `tp_clear`):** Resolves garbage collector leaks when cyclical references are attached to `ctx.state`, allowing the Python GC to reclaim C++ wrapped references safely.
* **String Interner:** C++ string interning (`interner.cpp`) eliminates string re-allocation for frequently accessed HTTP headers and method names.

### 2. `aquilia._dataengine` — ORM Hydration & Contract Validation
* **`FieldPlan` Contract Validation:** Compiles Contract schemas into native execution plans for `TextFacet`, `IntFacet`, `FloatFacet`, `BoolFacet`, `UUIDFacet`, `DateFacet`, `DateTimeFacet`, `TimeFacet`, `DecimalFacet`, `DurationFacet`, `BytesFacet`, and container types (`LIST`, `SET`, `TUPLE`, `DICT`).
* **Per-Field Eligibility & Escape Path:** When a Contract contains a field that cannot be represented natively (such as a custom Python predicate), that single field is escaped to the pure-Python `Sigil` while all sibling fields continue running on the native C++ plan.
* **`RowPlan` ORM Hydration:** Converts raw database rows into Python model instances directly in C++, accelerating `Model.objects.get()` by **13×** (120.7 µs → 9.3 µs).

### 3. `aquilia._json` — First-Party Native JSON Engine
* Backed by vendored [yyjson](https://github.com/ibireme/yyjson) 0.10.0 (MIT licensed).
* **Heap Work Stack:** Uses iterative stack traversal instead of recursive calls during encoding and decoding, preventing stack-overflow crashes from adversarial deeply-nested JSON payloads.
* **Thread-Local Buffer Pools:** Pre-allocates reusable memory buffers, drastically reducing memory allocator churn on heavy API response paths.
* **SWAR Vectorized Escaping:** Scans strings word-at-a-time using SIMD-like SWAR operations for fast byte escaping.
* **Framework Entrypoint (`aquilia.json`):** Unified `dumps()` (returning `bytes`) and `loads()` (accepting `bytes | bytearray | memoryview | str`), eliminating inconsistent third-party JSON library dependencies.

---

## Inline SQLite Execution (`aquilia.sqlite._inline`)

In SQLite, short indexed queries (`SEARCH` plan nodes) often cost less work to execute (~1.5 µs) than the thread-hopping overhead of dispatching to an async thread pool (~27 µs).

Aquilia v1.4.0 inspects `EXPLAIN QUERY PLAN` output:
* Queries confirmed to be bounded index seeks are executed inline on the event loop.
* Any statement measured to take longer than `inline_max_duration_ms` is permanently demoted to the thread pool.
* Configurable via `Workspace.database(inline_fast_queries=True|False)`.

---

## Configuration & Control (`AquilaConfig.Accelerator`)

You can control native engine activation via configuration, environment variables, or CLI flags.

### In `workspace.py`:
```python
from aquilia import AquilaConfig, Workspace

class Config(AquilaConfig):
    class Accelerator:
        engine: bool = True       # C++ router & RequestContext
        dataengine: bool = True   # C++ ORM hydration & FieldPlan
```

### CLI Flags:
```bash
# Force pure-Python execution
aq run --no-engine --no-dataengine

# Force native acceleration
aq run --engine --dataengine
```

### Environment Variables:
```bash
AQUILIA_ENGINE=1
AQUILIA_DATAENGINE=1
```

---

## Fail-Soft Architecture & Portability

All native extensions are **strictly optional**:
1. **Compilation Fallback:** When building from source without a C++20 compiler (`AQUILIA_ENGINE_OPTIONAL=ON`), CMake issues a build warning and falls back to packaging pure Python modules.
2. **Runtime Loaders (`_core_loader`, `_dataengine_loader`):** If a shared library is missing or an ABI mismatch occurs, the loader seamlessly binds the pure-Python implementation without crashing.
3. **Windows Portability:** Windows release wheels are built with Visual Studio 2022 and statically link the MSVC runtime, eliminating external runtime DLL dependencies.
