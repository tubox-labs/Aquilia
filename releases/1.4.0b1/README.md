# Aquilia v1.4.0b1 Release Notes — "Foredeck Watch"

Aquilia v1.4.0b1 continues the "Foredeck Watch" beta cycle, introducing major performance and correctness improvements across the core framework. This release brings three new native C++ extensions (`_core`, `_dataengine`, and `_json`), a native radix-trie router, per-field eligibility for native validation, and significant Dependency Injection (DI) and JSON engine optimizations. The primary focus of this release was hot-path correctness and performance, merging changes from `feature/aquilia-core-engine` and `perf/json-orm-validation-engine` branches.

## Table of Contents

1. [Native Engines](native_engines.md)
   * Three native C++ extensions: `_core`, `_dataengine`, `_json`.
   * Architecture, fail-soft loading, and `AQUILIA_ENGINE_OPTIONAL=ON`.
   * Build system details: CMake, nanobind, scikit-build-core.
2. [Performance](performance.md)
   * Phase 0 hot-path fixes: validate_body double-bind, Response.json str->bytes, _check_json_depth recursion.
   * SQLite inline execution (`inline_fast_queries`).
   * JSON engine, router, DI, controller, and ASGI optimizations.
3. [Validation Engine](validation_engine.md)
   * Native validation engine for contracts (`FieldPlan`).
   * Per-field eligibility (`CompiledPlan(plan, escaped)`).
   * Native TypeCodes and Container kinds.
4. [JSON Engine](json_engine.md)
   * Native JSON engine backed by `yyjson` 0.10.0.
   * Architecture: decode.cpp, encode.cpp, escape.hpp, numeric.hpp, buffer.hpp.
   * Bugs fixed during development.
5. [Bug Fixes](bug_fixes.md)
   * Root-cause analysis for request/response correctness fixes.
   * GC leak fixes (RequestContext tp_traverse/tp_clear).
6. [Migration Guide](migration.md)
   * `DISettings._strict_scopes` renamed to `strict_scopes`.
   * Upgrade checklist, compatibility matrix, and optional native extensions.
7. [Build & Distribution](build_and_distribution.md)
   * Multi-platform wheels via `cibuildwheel`, `scikit-build-core` + `nanobind`.
   * CMakeLists.txt structure and pyproject.toml changes.

---

## Key Goals

1. **Massive Performance Boosts and Hot-Path Optimizations.**
   The fundamental goal of v1.4.0b1 was identifying and rectifying hot-path bottlenecks. Measured improvements include up to 733% faster validation throughput (jumping from 1,809 RPS to 15,075 RPS) purely from addressing double-binding and double-encoding issues. ORM `get()` latency dropped by 13x (120.7µs to 9.3µs) due to the new SQLite inline execution model.

2. **Native C++ Core Enhancements (`_core`, `_dataengine`, `_json`).**
   Python overhead in tightly bound loops and parsing stages has been offloaded to three new C++ extensions. These extensions power a string interner, radix-trie router, request context, UUID parser, FieldPlan validation engine, RowPlan hydration engine, and a complete JSON codec.

3. **Optimized Zero-Dependency JSON Handling.**
   By vendoring `yyjson 0.10.0`, Aquilia achieves world-class JSON parsing and emission speeds directly within the framework. A unified `aquilia/json.py` entry point replaces the complex three-tiered third-party codec fallback chain (orjson -> ujson -> json), removing core dependencies while increasing throughput and safety (e.g., using a heap work stack rather than recursion for serialization).

4. **Resilient Per-Field Validation Engine.**
   The older validation engine was brittle: if a single field in a complex model could not be represented natively, the *entire* contract was demoted to the slow Python path. The new `FieldPlan` engine introduces per-field eligibility. Fields that are natively representable run in C++, while only unsupported fields gracefully escape to Python. This prevents systemic performance degradation.

5. **Fail-Soft Architecture and Seamless Distribution.**
   Despite introducing heavily optimized C++ components, Aquilia remains fully functional without them. Through `AQUILIA_ENGINE_OPTIONAL=ON` and fail-soft loader modules (`_dataengine_loader.py`), the framework falls back to pure Python equivalents transparently. Distribution is handled via robust `cibuildwheel` pipelines, providing pre-compiled wheels for macOS, Linux, and Windows across multiple CPU architectures.

6. **Correctness and Memory Safety.**
   Beyond performance, critical bugs were resolved. The RequestContext garbage collection leak (which leaked exactly 1 RequestCtx per request) was identified as a limitation in `nanobind`'s `inst_traverse` and fixed via custom `tp_traverse`/`tp_clear` slot methods. Issues with double-encoding payloads and unsafe recursive JSON depth checking were entirely rewritten.

---

## Performance Summary

The following table highlights the quantitative improvements verified during the `perf/json-orm-validation-engine` branch benchmarking:

| Metric | Before | After | Improvement | Note / Root Cause |
|---|---|---|---|---|
| **Validation RPS** | 1,809 | 15,075 | **+733%** | Fixed `validate_body` double-binding / cached parse |
| **ORM `get()` Latency** | 120.7 µs | 9.3 µs | **13x faster** | SQLite inline execution (thread-hop removed) |
| **DB Single Queries** | - | - | **+228%** | `_notify_inspector` gating & inline queries |
| **DB Queries (General)** | - | - | **+485%** | General SQLite pool overhead reduction |
| **DB Updates** | - | - | **+164%** | Fast-path execution & `asyncio.wait_for` removal |
| **JSON Encode (Small)** | - | - | **8.5x faster** | `_json` encode.cpp (direct emitter) |
| **JSON Encode (100KB)** | - | - | **3.9x faster** | `_json` + `Response.json` str->bytes fix |
| **JSON Encode (500 rows)** | - | - | **4.9x faster** | `buffer.hpp` thread-local pool |
| **JSON Decode (Small)** | - | - | **4.8x faster** | `_json` decode.cpp (yyjson arena) |
| **DI Resolve Overhead** | 66.8 ns | 22.9 ns | **~3x faster** | `DISettings.strict_scopes` slot field conversion |

*(Note: Validation time dropped from ~500s to ~200s in standard benchmark suite scenarios).*

---

## Highlights by Feature Area

### Native Extensions
- **`_core`**: String interner (`interner.cpp`), radix-trie router (`router.cpp`), native RequestContext.
- **`_dataengine`**: UUID parser (`uuid_parse.cpp`), FieldPlan validation (`fieldplan.cpp`), RowPlan hydration (`rowplan.cpp`).
- **`_json`**: yyjson integration (`decode.cpp`, `encode.cpp`, `escape.hpp`, `numeric.hpp`, `buffer.hpp`).

### Routing and Controller Optimization
The router has been fully rewritten from a Python regex-based approach to a native C++ radix-trie (`aquilia/_core/src/router.cpp`). This router supports per-method eligibility checks directly within the traversal logic, significantly reducing overhead for endpoints with heavy traffic. The ASGI layer now uses direct cache writes instead of the slow `register_instance` method, and type hint processing is heavily hoisted and cached at startup.

### Database Engine (SQLite)
The default SQLite thread pool was found to be a massive bottleneck for fast, index-bound queries (costing 27µs for the thread hop alone compared to ~1.5µs of actual work). The new `sqlite/_inline.py` engine safely executes fast queries directly on the asyncio event loop, permanently demoting slower queries back to the thread pool based on the `inline_max_duration_ms` threshold.

### Contracts and Validation
The integration of `FieldPlan` into `Sigil.validate` means contracts are compiled at server startup. The framework categorizes each field. Fields with supported TypeCodes (like `STR`, `INT`, `UUID`, `DATETIME`, etc.) and ContainerKinds (like `LIST`, `DICT`) are packed into a fast-path native evaluator. Complex facets (like custom validators or unsupported regex) are identified as "escaped" and processed seamlessly in Python.

---

## What Changed Internally?

- **Dependency Injection**: The `Container.resolve_async()` method hoisted `provider.meta` accesses, dropping property reads from 11x down to 1. 
- **Garbage Collection**: Fixed cyclic references in `RequestContext` by implementing raw Python C-API slot methods, ensuring memory remains flat over millions of requests.
- **Dependency Graph**: Removed reliance on third-party JSON codecs.

Please read the subsequent documents in this release for a thorough technical breakdown of each area.
