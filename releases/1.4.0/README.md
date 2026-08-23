# Aquilia v1.4.0 Release Notes — "Grand Armada"

Aquilia v1.4.0 is the **flagship milestone release** of the framework. It consolidates seven beta cycles (`v1.4.0b0` through `v1.4.0b6`) into a production-grade, hardened, stable release.

v1.4.0 introduces optional native C++ acceleration extensions (`_core`, `_dataengine`, `_json`), the embedded `aquilia.vectordb` vector search subsystem, the native ASGI Development Platform (`aquilia.devplatform`), a complete restructuring of the HTTP middleware package, a dedicated WebSocket middleware pipeline, a modernized CLI architecture with unified health checks, complete CPython 3.10–3.14 compatibility with multi-platform binary wheels, and 100% typed static exports for seamless IDE autocomplete and developer ergonomics.

```bash
pip install --upgrade aquilia==1.4.0
```

---

## Flagship Pillars of v1.4.0

```
                        ┌───────────────────────────────────────────────────────────┐
                        │                 Aquilia 1.4.0 Grand Armada                │
                        └─────────────────────────────┬─────────────────────────────┘
                                                      │
         ┌────────────────────────┬───────────────────┼───────────────────┬────────────────────────┐
         │                        │                   │                   │                        │
         ▼                        ▼                   ▼                   ▼                        ▼
┌──────────────────┐    ┌──────────────────┐┌──────────────────┐┌──────────────────┐    ┌──────────────────┐
│ Native C++20     │    │ Vector Database  ││ Native ASGI Dev  ││ Composable       │    │ Modernized CLI   │
│ Accelerators     │    │ Subsystem        ││ Platform (ADP)   ││ Middleware Stacks│    │ & Health Checks  │
│ (_core/_data/_json)│  │ (aquilia.vectordb)││ (h11 & RFC 6455) ││ (HTTP & Sockets) │    │ (ExitCode/Checks)│
└──────────────────┘    └──────────────────┘└──────────────────┘└──────────────────┘    └──────────────────┘
```

1. **Native C++20 Acceleration Engines (`aquilia/_core`, `aquilia/_dataengine`, `aquilia/_json`)**
   High-performance optional native extensions built with `nanobind` and `scikit-build-core`. Features a radix-trie router, a 7-slot zero-allocation `RequestContext`, a native `FieldPlan` contract validator, a native `RowPlan` ORM hydrator, and a first-party JSON engine powered by vendored `yyjson` 0.10.0. All extensions are strictly fail-soft: compiler-free installs automatically degrade to pure Python.

2. **Embedded Vector Database Subsystem (`aquilia.vectordb`)**
   Declarative `VectorModel` schema, unified field descriptors, multi-syntax query filtering (keyword, `VF` tree, operator-overloaded field expressions, and safe string `EQL`), pluggable embedders, chunking provenance, quantization (`sq8`, `pq`, `opq`), GPU policy management, and single-query SQL-ORM hybrid mirroring (`@mirror`, `as_models()`).

3. **Native ASGI Development Platform (`aquilia.devplatform` / ADP)**
   Purpose-built local development server with an `h11`-based HTTP/1.1 transport, dependency-free RFC 6455 WebSocket engine, AST-based dependency-graph hot reload, and per-request cProfile CPU profiling wired directly into ASGI request connection lifecycles.

4. **Restructured HTTP Middleware & WebSocket Pipeline**
   Clean leaf-zone architecture in `aquilia.middleware` preventing circular imports, declarative hook-based lifecycle (`before`, `after`, `handle`, `should_run`), and a dedicated 3-hook `SocketMiddlewareStack` for real-time WebSockets with 7 built-in production middleware.

5. **Modernized CLI Architecture & Unified Health Checks**
   Centralized process exit codes via `ExitCode`, structured `CliFault` error handling, and the extensible `aquilia.cli.checks` engine running automated diagnostics across 16 subsystems for `aq doctor` and `aq validate`.

6. **IDE Code Intelligence & Typing Parity**
   Static `if TYPE_CHECKING:` barrel exports in `aquilia/__init__.py` guaranteeing instant autocomplete, signature help, docstrings, and direct Go-to-Definition navigation across all 594 public exports in VS Code, PyCharm, and Mypy, with zero runtime import overhead.

---

## Detailed Documentation Pages

- [Native C++ Acceleration Engines](native_engines.md) — Architecture of `_core`, `_dataengine`, `_json`, inline SQLite, and fail-soft loaders.
- [Vector Database Subsystem](vectordb.md) — Models, field descriptors, query engine, EQL grammar, embedders, chunking, and CLI tools.
- [Native Development Platform (ADP)](devplatform.md) — HTTP/1.1 transport, RFC 6455 WebSockets, AST hot-reload, and CPU profiling.
- [Middleware & WebSockets](middleware_and_websockets.md) — Package restructure, hook lifecycles, and the WebSocket middleware pipeline.
- [CLI Architecture & Unified Health Checks](cli_and_checks.md) — `ExitCode`, `CliFault`, `aq doctor`, `aq validate`, and route compilation.
- [Bug Fixes & Security Hardening](bug_fixes.md) — Complete inventory of fixes across controllers, rate limiting, migrations, and memory leaks.
- [Migration & Upgrade Guide](migration.md) — Step-by-step upgrade guide from v1.3.x and beta releases to v1.4.0 stable.

---

## Performance Benchmarks

All figures measured with `oha`, 50 concurrent connections, 5 seconds duration, macOS Apple Silicon:

| Scenario | v1.3.10 (Pure Python) | v1.4.0 (Grand Armada) | Improvement |
| :--- | :--- | :--- | :--- |
| **Database Single (`db_single`)** | 5,797 rps | 19,034 rps | **+228% (3.3×)** |
| **Database Queries (`db_queries`)** | 1,496 rps | 8,759 rps | **+485% (5.8×)** |
| **Database Updates (`db_updates`)** | 744 rps | 1,965 rps | **+164% (2.6×)** |
| **Contract Validation (`validation`)** | 1,809 rps | 15,075 rps | **+733% (8.3×)** |
| **ORM Entity Hydration (`get()`)** | 120.7 µs | 9.3 µs | **13× faster** |
| **JSON Serialization (Small)** | 0.76 µs | 0.09 µs | **8.5× faster** |
| **JSON Deserialization (Small)** | 0.62 µs | 0.13 µs | **4.8× faster** |
| **DI Scope Check Resolution** | 66.8 ns | 22.9 ns | **3× faster** |

---

## Compatibility Matrix

| Runtime / OS | Supported Versions | Notes |
| :--- | :--- | :--- |
| **Python** | 3.10, 3.11, 3.12, 3.13, 3.14 | Tested natively across entire test matrix |
| **Linux** | x86_64, aarch64 (glibc 2.28+) | Binary wheels available on PyPI |
| **macOS** | Apple Silicon (arm64), Intel (x86_64) | macOS 10.15+ deployment target |
| **Windows** | AMD64 (Windows 10/11, Server 2019+) | Static MSVC runtime linkage (Visual Studio 2022) |
| **Vector DB (`elips`)** | Python 3.11–3.14 | Optional extra (`pip install 'aquilia[vectordb]'`) |
