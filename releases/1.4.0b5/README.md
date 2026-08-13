# Aquilia v1.4.0b5 Release Notes — "Stable Bearings"

Aquilia v1.4.0b5 is a compatibility and release-engineering beta focused on making the native acceleration layer trustworthy on real installations. It adds CPython 3.14 support, repairs Windows wheel portability, makes compiler-free source installs genuinely fail-soft, and fixes two Python runtime regressions in controller dispatch and Contract annotation evaluation.

## Documentation Set

1. [Release Overview](README.md)
2. [Native Wheels and Source Builds](native_packaging.md)
3. [Controller Dispatch Correctness](controller_dispatch.md)
4. [Contract Safety on Python 3.14](contract_safety.md)
5. [CI and Release Pipeline](ci_release_pipeline.md)
6. [Bug Fixes and Internal Refactoring](bug_fixes.md)
7. [Migration and Upgrade Guide](migration.md)

## Release Overview

The previous Windows wheel could pass CI and still fail when installed on a normal Windows machine. The `.pyd` files were built on a runner using a newer preview MSVC environment and depended on runtime DLLs that were available on the runner but not necessarily on user systems. At the same time, the intended pure-Python fallback for source distributions was unreachable when no compiler existed because CMake enabled C and C++ in the top-level `project()` call before the optional-build branch ran.

v1.4.0b5 corrects both sides of that contract:

- Release wheels must contain and load `_core`, `_dataengine`, and `_json`.
- Windows wheels are built with Visual Studio 17 2022 and a static MSVC runtime.
- Source installs may omit all native modules when no C/C++ compiler exists.
- CI verifies the installed wheel outside the repository checkout.
- CPython 3.14 is part of the tested and published wheel matrix.

## Highlights

### Reliable Windows Native Wheels

Windows AMD64 wheel builds are pinned to `windows-2022` and the `Visual Studio 17 2022` generator. Every native target, including support libraries created by nanobind, receives the static MSVC runtime setting. This removes the accidental dependency on preview Visual C++ runtime DLLs.

See [Native Wheels and Source Builds](native_packaging.md).

### Compiler-Free Installs Work

The top-level CMake project now starts with `LANGUAGES NONE`, probes C and C++, and calls `enable_language()` only after both compilers have been found. With `AQUILIA_ENGINE_OPTIONAL=ON`, configuration returns successfully and scikit-build-core packages the Python implementation.

### CPython 3.14 Support

Project classifiers, CI, release smoke tests, and cibuildwheel now cover CPython 3.14. Windows, Linux, and macOS test matrices include 3.14 where applicable, and release verification requires a Windows AMD64 wheel for each CPython version from 3.10 through 3.14.

### Correct Sync and Async Controller Dispatch

`ControllerEngine` no longer caches coroutine status by `id(bound_method)`. Bound method objects are temporary, and CPython may reuse their IDs for unrelated methods. The engine now calls a handler once and awaits the returned object only when `inspect.isawaitable()` is true.

See [Controller Dispatch Correctness](controller_dispatch.md).

### Contract Security Faults Remain Visible

On Python 3.14, deferred annotation evaluation can occur while `ContractMeta` reads `cls.__annotations__`. A `CastFault` raised during that evaluation is now re-raised rather than swallowed by generic annotation-introspection recovery. Unsafe facet definitions, including ReDoS-prone patterns, retain definition-time failure semantics.

See [Contract Safety on Python 3.14](contract_safety.md).

## Framework and Developer Experience Improvements

- Installing from an sdist on a machine without Visual Studio Build Tools, GCC/G++, or Xcode command-line tools now yields a usable package instead of a CMake configure failure.
- Native wheel diagnostics report the resolved package path and the status of each extension.
- Decorators that are synchronous functions but return awaitables work correctly as route handlers.
- Controller handlers are never invoked twice as part of coroutine detection.
- Python 3.14 Contract classes preserve the same security validation behavior as earlier supported Python versions.

## Performance Improvements

No new native algorithms are introduced. Windows wheels now consistently activate the existing acceleration paths instead of falling back after a DLL load failure. Pure-Python fallback installs remain functionally compatible but do not receive native routing, field-plan, or yyjson acceleration.

The controller change removes an unsafe cache lookup and performs one `inspect.isawaitable()` check per handler result. The correctness gain outweighs the negligible constant-time inspection cost.

## CLI and Configuration Compatibility

No `aq` commands, flags, exit codes, workspace fields, integration types, or `AquilaConfig.Accelerator` fields changed in this release.

Build-time `AQUILIA_ENGINE_OPTIONAL` and runtime `AQUILIA_ENGINE` / `AQUILIA_DATAENGINE` serve different purposes:

- `AQUILIA_ENGINE_OPTIONAL` controls whether a source build may omit extensions.
- Runtime accelerator settings control whether installed extensions are loaded.

## Breaking Changes

There are no intentional public API breaks.

CI pipelines that previously allowed a wheel to omit native modules silently may now fail. This is an intentional tightening of the release contract, not an application runtime incompatibility. Code that depended on unsafe Contract definitions being silently accepted will now fail at class creation.

## Security Improvements

- Deferred annotation evaluation can no longer hide `CastFault` validation or regex ReDoS failures.
- Release tests import from outside the source checkout, preventing path shadowing from producing false-positive native checks.
- Release artifacts are rejected when any supported Windows CPython wheel is missing.

## Deprecated and Removed Features

No public features are deprecated or removed. The private controller `_is_coro_cache` was removed because its identity key was unsound; private internals are not covered by compatibility guarantees.

## Compatibility Matrix

| Component | Supported |
|---|---|
| Python | CPython 3.10–3.14 |
| Windows wheels | AMD64, stable VS 2022 ABI |
| Linux wheels | x86_64 and aarch64 |
| macOS wheels | x86_64 and arm64 |
| Source install without compiler | Supported through pure-Python fallback |
| Native source build | CMake 3.21+, C++20 compiler |

## Known Issues

- A pure-Python source install is slower for workloads that benefit from native routing, hydration, or JSON serialization.
- Native modules are CPython-version and architecture specific; copying `.pyd` or shared-library files between environments is unsupported.
- Linux aarch64 wheel builds use QEMU in CI and are significantly slower than native-architecture jobs.
- Free-threaded and no-GIL CPython variants are not included in this beta's wheel matrix.

## Upgrade Instructions

```bash
python -m pip install --upgrade --no-cache-dir "aquilia==1.4.0b5"
python -c "import aquilia; print(aquilia.__version__)"
```

Windows users affected by a beta DLL error should use `--no-cache-dir` or `--force-reinstall` so pip does not reuse the older wheel.

See the full [Migration and Upgrade Guide](migration.md).

## Upgrade Checklist

- [ ] Pin or install `aquilia==1.4.0b5`.
- [ ] On Windows, reinstall without pip's wheel cache.
- [ ] Run native diagnostics if acceleration is required.
- [ ] Run controller tests containing both `def` and `async def` handlers.
- [ ] Run Contract definition/security tests under Python 3.14.
- [ ] Update custom release CI to distinguish strict wheel builds from optional source installs.

## Documentation Improvements

- Added the aqdocx [Native Extensions](/docs/native-extensions) guide.
- Updated installation, controller engine, Contract annotations/faults, configuration, and testing documentation.
- Updated the documentation site version, announcement, release cards, and timeline.
- Added this multi-page release documentation and a detailed changelog entry.

## Credits

Thanks to the Windows users and CI evidence that exposed the gap between “wheel built” and “wheel imports on a clean machine.” The fix is backed by installed-wheel tests, compiler-free sdist tests, controller regression tests, and Contract security regression tests.
