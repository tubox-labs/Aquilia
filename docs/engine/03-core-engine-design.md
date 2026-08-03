# Phase 3 — Native Core Engine Design

**Status:** design
**Depends on:** Phase 1 (architecture audit), Phase 2 (performance audit)
**Implements:** `aquilia/_core/` — the C++20 shared library loaded at import time

---

## 1. Mandate

Phase 2 established that a native router+DI engine has a **5.5% end-to-end ceiling**. The mandate is therefore broader: a native *request-context engine* that eliminates the dominant measured costs:

| Target | Measured cost | Mechanism |
|---|---|---|
| `register_instance(Request)` per request | 3.68 µs (22%) | Native `RequestContext` replaces ValueProvider+COW |
| `get_type_hints()` uncached | 2.64 µs (16%) | Native binding cache keyed by handler id |
| `RequestCtx.__setattr__` ×24 | 1.26 µs (7.6%) | Native object, no Python `__setattr__` |
| `os.urandom` in pool | 0.72 µs (4.3%) | C++ CSPRNG, caller-provided id |
| Router `_version_matches` imports | 0.42 µs (2.6%) | Native router, no per-call imports |
| DI cached resolve `_unwrap_token` | 1.17 µs (DI-heavy) | Native resolver, plain-type fast path |

**Combined ceiling: ~10 µs saved → 16.49 µs → ~6.5 µs (~2.5× throughput).**

---

## 2. Constraints from Phase 1

1. **Import-cycle leaf.** The package graph is a single 40-node SCC. The native module must have zero `aquilia.*` imports — it is a dependency of `aquilia`, not a dependent.
2. **Post-lifespan compilation.** Route tables and DI graphs are not final until after `lifespan.startup`. The engine must be initialised at lifespan time, not at import time.
3. **Fail-soft.** Load failure must not crash the process. The Python fallback must remain fully functional.
4. **Protocol preservation.** All ten extension points from Phase 1 §9 must continue to work unchanged.
5. **GIL.** Python 3.11 (the target) uses the GIL. The native module may release it for pure-C++ work but must hold it when touching Python objects.

---

## 3. Module layout

```
aquilia/
  _core/                        ← C++20 source tree
    CMakeLists.txt
    src/
      arena.hpp / arena.cpp     ← bump allocator (per-request lifetime)
      interner.hpp              ← string interner (route segments, header names)
      router.hpp / router.cpp   ← radix trie + static hash map
      di_resolver.hpp / .cpp    ← DI cache + type-key interner
      request_ctx.hpp / .cpp    ← native RequestContext object
      binding_cache.hpp / .cpp  ← handler signature + type-hints cache
      module.cpp                ← nanobind entry point
    tests/
      test_arena.cpp
      test_router.cpp
      test_di_resolver.cpp
  _core.pyi                     ← stub for IDE / mypy
  _core_loader.py               ← fail-soft import wrapper
```

`_core_loader.py` is the only file in `aquilia/` that imports `_core`. Everything else imports from `_core_loader`, which catches `ImportError` and falls back to pure-Python equivalents.

```python
# aquilia/_core_loader.py
try:
    from aquilia._core import (
        RequestContext,
        RadixRouter,
        DIResolver,
        BindingCache,
    )
    _NATIVE = True
except ImportError:
    from aquilia._core_fallback import (   # pure-Python equivalents
        RequestContext,
        RadixRouter,
        DIResolver,
        BindingCache,
    )
    _NATIVE = False
```

---

## 4. Build system

**CMake + nanobind**, invoked via `scikit-build-core` so `uv pip install -e .` works.

```
pyproject.toml
  [build-system]
  requires = ["scikit-build-core>=0.9", "nanobind>=2.0"]
  build-backend = "scikit_build_core.build"

  [tool.scikit-build]
  cmake.build-type = "Release"
  wheel.packages = ["aquilia"]
```

`CMakeLists.txt` minimum:

```cmake
cmake_minimum_required(VERSION 3.21)
project(aquilia_core CXX)
set(CMAKE_CXX_STANDARD 20)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(_core
  src/arena.cpp
  src/router.cpp
  src/di_resolver.cpp
  src/request_ctx.cpp
  src/binding_cache.cpp
  src/module.cpp
)
target_include_directories(_core PRIVATE src)
```

**No external C++ dependencies.** All data structures are self-contained. `absl` or `robin_hood` are explicitly excluded — the wheel must build from source on any platform without network access.

---

## 5. Memory model

### 5.1 Per-request arena

```cpp
// arena.hpp
class Arena {
    static constexpr size_t BLOCK = 65536;
    std::vector<std::unique_ptr<char[]>> blocks_;
    char* cur_ = nullptr;
    size_t remaining_ = 0;
public:
    void* alloc(size_t n, size_t align = 8) noexcept;
    void reset() noexcept;   // O(1): resets pointers, keeps blocks
    ~Arena() = default;
};
```

One arena per request, reset (not freed) at request end. Holds: path-param strings, header value copies, binding-result temporaries. **Never holds Python objects** — those live on the Python heap and are referenced by `PyObject*` with normal refcount.

### 5.2 String interner

```cpp
// interner.hpp
class Interner {
    std::unordered_map<std::string_view, uint32_t> map_;
    std::vector<std::string> strings_;
public:
    uint32_t intern(std::string_view s);
    std::string_view get(uint32_t id) const noexcept;
};
```

Global singleton, populated at lifespan startup. Interns: route segment literals, HTTP method strings, header names, DI type-key strings. Interned IDs are used as array indices in the router and DI resolver, replacing string comparisons with integer comparisons.

---

## 6. Initialisation protocol

```python
# aquilia/server.py — inside AquiliaServer.startup()
if _NATIVE:
    from aquilia._core_loader import RadixRouter, DIResolver, BindingCache
    _native_router = RadixRouter()
    for route in compiled_routes:
        _native_router.add_route(route.method, route.full_path, route.id)
    _native_router.freeze()   # builds the trie, no further mutations

    _native_di = DIResolver(app_container)
    _native_di.freeze()

    _native_bindings = BindingCache()
    # pre-warm for all registered handlers
    for route in compiled_routes:
        _native_bindings.register(route.handler_id, route.parameters)
```

`freeze()` is a one-way transition: the object becomes immutable and thread-safe. Any call to `add_route` after `freeze()` raises `RuntimeError`. This matches the Phase 1 finding that the route table is final after lifespan startup.

---

## 7. Python object protocol

The native module exposes Python types via nanobind. All types use `nb::class_<>` with `__slots__`-equivalent layout. No `__dict__` on any native type.

```cpp
// module.cpp (excerpt)
NB_MODULE(_core, m) {
    nb::class_<RequestContext>(m, "RequestContext")
        .def(nb::init<>())
        .def_rw("request",    &RequestContext::request)
        .def_rw("identity",   &RequestContext::identity)
        .def_rw("session",    &RequestContext::session)
        .def_rw("auth",       &RequestContext::auth)
        .def_rw("container",  &RequestContext::container)
        .def_rw("state",      &RequestContext::state)
        .def_rw("request_id", &RequestContext::request_id)
        .def("get",           &RequestContext::get)
        .def("set",           &RequestContext::set);
    // ...
}
```

`RequestContext::state` is a `nb::dict` (Python dict) — the escape hatch for middleware that needs dynamic keys. `get`/`set` are the typed accessors for the known slots.

---

## 8. Fallback parity

`aquilia/_core_fallback.py` provides pure-Python classes with identical APIs. Every test in `tests/` runs against both the native and fallback implementations via a pytest fixture:

```python
# tests/conftest.py
@pytest.fixture(params=["native", "fallback"])
def engine(request):
    if request.param == "native" and not _NATIVE:
        pytest.skip("native engine not built")
    return _get_engine(request.param)
```

The fallback is not a stub — it is the current production code, refactored to match the native API. This means the native engine can be disabled at any time with zero behaviour change.

---

## 9. CI matrix

| Platform | Python | Build | Test |
|---|---|---|---|
| macOS arm64 | 3.11, 3.12 | Release | full |
| Linux x86_64 | 3.11, 3.12 | Release | full |
| Linux x86_64 | 3.11 | Debug + ASAN | full |
| Windows x64 | 3.11 | Release | full |

Wheels are built with `cibuildwheel`. The `_core` extension is optional — if the wheel build fails, the package installs without it and falls back to pure Python.

---

## 10. Success criteria

| Metric | Target | Measurement |
|---|---|---|
| Static route match | ≤ 200 ns | `benchmarks/engine/profile_baseline.py` |
| DI cached resolve | ≤ 200 ns | same |
| RequestContext acquire+reset | ≤ 100 ns | same |
| Full request (static, no params) | ≤ 7 µs | `benchmarks/engine/e2e_attribution.py` |
| Fallback parity | 100% test pass | `pytest tests/` with `_NATIVE=False` |
| No import cycle | zero new SCC members | `benchmarks/engine/import_graph.py` |
| Build from source | ≤ 60 s | CI timer |
