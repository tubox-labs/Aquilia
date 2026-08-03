# Phase 6 — Python Binding Architecture

**Status:** design
**Principle:** the binding layer is a thin translation shell. All logic lives in `src/*.cpp`; `module.cpp` contains no business rules.

---

## 1. Choice of binding library

| Option | Verdict |
|---|---|
| **nanobind 2.13** | **Selected.** ~4× smaller binaries and ~2× faster call overhead than pybind11; native `nb::dict` / `nb::object` handles; free-threading aware. Installed and verified in this repo. |
| pybind11 | Rejected — heavier call overhead, larger wheels, no advantage here. |
| raw CPython C-API | Rejected — hand-written refcounting across ~30 entry points is the highest-risk part of the whole project for no measured gain. |
| Cython | Rejected — we need a reusable C++ core (Phase 3 mandate), not generated C glue. |
| ctypes/cffi | Rejected — per-call FFI overhead (~1 µs) exceeds the costs we are trying to remove. |

Call overhead matters directly: the engine is invoked 4–6 times per request, so a 100 ns-per-call difference is 0.5 µs/request — comparable to the entire routing cost we are optimising.

---

## 2. Module organisation

```
src/module.cpp          ← the ONLY file that includes <nanobind/nanobind.h>
    ├── bind_arena()        (diagnostics only)
    ├── bind_interner()     (diagnostics only)
    ├── bind_router()
    ├── bind_di_resolver()
    ├── bind_request_ctx()
    └── bind_binding_cache()
```

Core headers (`router.hpp`, `di_resolver.hpp`, …) are **Python-agnostic except where they must hold `PyObject*`**. Where a Python reference is unavoidable (the DI cache stores resolved instances), the header uses an opaque `PyRef` wrapper defined in `pyref.hpp` rather than nanobind types, so core logic stays unit-testable from plain C++ (`tests/test_router.cpp` links without Python).

```cpp
// pyref.hpp — minimal owning reference, no nanobind dependency
class PyRef {
    PyObject* p_ = nullptr;
public:
    PyRef() = default;
    explicit PyRef(PyObject* p, bool steal = false) noexcept;
    PyRef(const PyRef&) noexcept;              // incref
    PyRef(PyRef&&) noexcept;                   // steal
    ~PyRef() noexcept;                         // decref
    PyObject* get() const noexcept { return p_; }
};
```

---

## 3. Ownership and lifetime

| Object | Owner | Lifetime |
|---|---|---|
| `RadixRouter` | Python (`nb::class_`) | held by `AquiliaServer`; freed on GC |
| `DIResolver` | Python | one per app container |
| `RequestContext` | Python | one per request, recycled by native freelist |
| `Interner` | C++ static, ref-counted by module | process lifetime |
| `Arena` | owned by its `RequestContext` | reset per request |
| Interned strings | `Interner` | process lifetime (never freed) |
| Cached `PyObject*` in `DIResolver` | `PyRef` (strong) | until scope clear / resolver destruction |
| Route metadata objects | **Python** | native side stores only `uint32 route_id` |

**Rule: the native engine never owns framework objects.** It stores dense integer ids and hands them back; the Python layer maps id → `CompiledRoute`. This is what makes the fallback trivially equivalent and keeps GC semantics unchanged.

`nb::class_` types use `nb::is_final()` to prevent Python subclassing, which would break the fixed layout assumptions.

---

## 4. GIL policy

| Operation | GIL |
|---|---|
| `router.match(method, path)` | **held** — returns Python `str`/`int` params |
| `router.add_route(...)`, `freeze()` | held (startup only) |
| `resolver.get(token_id)` | held — returns borrowed `PyObject*` |
| `ctx.reset()` / `bind_request()` | held — touches `PyObject*` slots |
| `interner.intern(...)` during freeze | released for the pure-C++ portion |
| trie construction inside `freeze()` | **released** — no Python objects touched |

Only `freeze()` releases the GIL, via `nb::gil_scoped_release`, and only around the segment-sort/flatten phase. Every hot-path entry point holds the GIL because it must produce or consume Python objects; releasing and re-acquiring would cost more (~100 ns) than the work performed.

**No native code calls back into Python.** This is an explicit invariant: it removes all re-entrancy and GIL-ordering hazards, and it is enforceable by review because `module.cpp` is the only Python-aware translation unit.

---

## 5. Exception translation

C++ exceptions must never cross the ABI boundary. Every binding is wrapped:

| C++ | Python |
|---|---|
| `std::bad_alloc` | `MemoryError` |
| `std::out_of_range` | `IndexError` |
| `EngineFrozen` | `RuntimeError` |
| `EngineNotFrozen` | `RuntimeError` |
| `RouteConflict` | `ValueError` (Python re-raises as `RoutingFault`) |
| any other `std::exception` | `RuntimeError` with `what()` |

Domain errors are **not** raised from C++. Per Phase 4 §9, the native layer signals failure by return value (`nullptr`, `NO_ROUTE`, `false`) and the Python layer raises the existing structured `Fault` subclasses with their full diagnostic payloads. This preserves the Phase 1 §9 invariant that all framework errors are `Fault`s with stable codes.

```cpp
nb::register_exception_translator([](const std::exception_ptr& p, void*) {
    try { std::rethrow_exception(p); }
    catch (const EngineFrozen& e) { PyErr_SetString(PyExc_RuntimeError, e.what()); }
    catch (const std::bad_alloc&) { PyErr_SetString(PyExc_MemoryError, "engine allocation failed"); }
});
```

---

## 6. Zero-copy opportunities

| Data | Approach |
|---|---|
| request path | `nb::str` → `PyUnicode_AsUTF8AndSize`, borrowed `string_view`, no copy |
| HTTP method | interned id resolved from a 9-entry perfect hash on the borrowed buffer |
| path segments | `string_view` slices of the path buffer — no split, no list |
| param values | `(offset, length)` pairs on the C++ stack; Python objects built **only on match** |
| route metadata | never crosses — `uint32` id only |
| DI instances | borrowed `PyObject*`, one incref on cache insert |

The path buffer is guaranteed alive for the duration of the call because the caller (Python) holds the `str`. No native structure retains a `string_view` past the call.

---

## 7. ABI and wheel strategy

**Decision: build per Python minor version, not against the Stable ABI (`Py_LIMITED_API`).**

Rationale: nanobind requires CPython internals unavailable under the limited ABI, and the hot path needs `PyUnicode_AsUTF8AndSize` and direct `PyLong` construction. The cost is a larger wheel matrix, which `cibuildwheel` handles mechanically.

| Axis | Values |
|---|---|
| Python | 3.11, 3.12, 3.13 |
| Linux | `manylinux_2_28` x86_64, aarch64 |
| macOS | 11.0+ universal2 (x86_64 + arm64) |
| Windows | AMD64 |

`aquilia` declares `requires-python = ">=3.10"`. Python 3.10 is **not** in the native matrix — it receives the pure-Python fallback. This is acceptable precisely because the fallback is the current production code (Phase 3 §8), so 3.10 users see today's behaviour and today's performance.

`_core.abi3` is not produced. The extension filename carries the interpreter tag, so a wheel installed on a mismatched interpreter simply fails to import and the loader falls back.

---

## 8. Packaging

The extension is **optional**. `pyproject.toml` moves to `scikit-build-core`, but the build is configured so that a compiler failure degrades to a pure-Python wheel rather than failing the install:

```toml
[build-system]
requires = ["scikit-build-core>=0.9", "nanobind>=2.0"]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
cmake.build-type = "Release"
wheel.packages = ["aquilia"]
cmake.define.AQUILIA_ENGINE_OPTIONAL = "ON"
```

Sdist installs on a machine without a C++20 compiler produce a working (fallback) install. This is the packaging expression of the Phase 1 §2 fail-soft constraint.

`MANIFEST.in` gains `recursive-include aquilia/_core *.hpp *.cpp CMakeLists.txt` so sdists can rebuild.

---

## 9. CI/CD

```yaml
# .github/workflows/engine.yml (sketch)
build_wheels:
  strategy:
    matrix:
      os: [ubuntu-latest, macos-14, windows-latest]
  steps:
    - uses: pypa/cibuildwheel@v2
      env:
        CIBW_BUILD: "cp311-* cp312-* cp313-*"
        CIBW_TEST_COMMAND: >
          pytest {project}/tests -q -x
          && python -c "from aquilia._core_loader import _NATIVE; assert _NATIVE"

sanitizers:
  runs-on: ubuntu-latest
  steps:
    - run: cmake -DCMAKE_BUILD_TYPE=Debug -DAQUILIA_SANITIZE=address,undefined
    - run: ctest --output-on-failure          # pure-C++ unit tests
    - run: pytest tests/ -q                  # Python tests under ASAN

fallback_parity:
  steps:
    - run: AQUILIA_ENGINE=0 pytest tests/ -q # full suite, native disabled
```

Three gates, all blocking: wheels build and import natively on every target; ASAN/UBSAN clean; the full suite passes with the engine disabled.

---

## 10. Acceptance criteria

| Criterion | Target |
|---|---|
| Binding call overhead | ≤ 60 ns per entry point |
| `module.cpp` contains no logic | review gate — only `nb::` glue |
| Native code calling into Python | zero occurrences (grep gate) |
| Refcount correctness | ASAN + `sys.gettotalrefcount` delta ≈ 0 over 10k requests |
| Wheel builds | 3 OS × 3 Python, all green |
| Install without compiler | succeeds, `_NATIVE is False` |
| Full suite with engine disabled | 100% pass |
