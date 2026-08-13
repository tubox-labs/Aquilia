# Bug Fixes and Internal Refactoring — v1.4.0b5

## Fixed

### Windows native modules failed after a successful pip install

- **Previous behavior:** `_core`, `_dataengine`, and `_json` could report `DLL load failed` on ordinary Windows systems.
- **Root cause:** wheels were built against a preview toolchain/runtime present on CI but absent on user machines.
- **New behavior:** Windows wheels use VS 2022 and static runtime linkage.
- **User impact:** installed release wheels activate native acceleration without requiring a matching preview redistributable.

### Missing compilers aborted optional source installs

- **Previous behavior:** CMake failed at the top-level `project()` call before optional fallback logic ran.
- **Root cause:** C and C++ were enabled unconditionally.
- **New behavior:** languages are probed first; optional builds return successfully when compilers are absent.
- **User impact:** `pip install` from an sdist works on machines without C/C++ build tools.

### CI could test source code instead of the installed wheel

- **Previous behavior:** the checkout could appear first on `sys.path`, hiding packaging or DLL problems.
- **Root cause:** native assertions ran from the project directory.
- **New behavior:** the installed-wheel check changes to a temporary directory and removes the checkout path.
- **User impact:** published artifacts receive a meaningful import test.

### Release builds silently degraded to Python

- **Previous behavior:** setting `AQUILIA_ENGINE_OPTIONAL=OFF` as a regular environment variable did not override the scikit-build CMake definition.
- **Root cause:** CMake definitions and process environment variables are distinct configuration channels.
- **New behavior:** cibuildwheel passes `CMAKE_ARGS=-DAQUILIA_ENGINE_OPTIONAL=OFF`.
- **User impact:** a wheel missing an extension fails CI instead of passing with skipped native tests.

### Sync controller return values were sometimes awaited

- **Previous behavior:** a dictionary returned by a sync handler could raise `TypeError: 'dict' object can't be awaited`.
- **Root cause:** coroutine classification was cached by the unstable ID of a temporary bound method.
- **New behavior:** the handler is called once and only an awaitable result is awaited.
- **User impact:** mixed sync/async controllers and decorator wrappers behave deterministically.

### Python 3.14 could hide Contract definition faults

- **Previous behavior:** a deferred annotation `CastFault` could be swallowed by generic introspection recovery.
- **Root cause:** annotation evaluation moved inside the metaclass access path on Python 3.14.
- **New behavior:** `CastFault` propagates through both recovery blocks.
- **User impact:** invalid/security-sensitive facets fail at class creation as designed.

## Internal Refactoring

- Removed the private `_is_coro_cache` and its cache-clear branch.
- Added a reusable installed-wheel native verification tool.
- Scoped wheel generator configuration by platform so Ninja remains available for fallback configuration while Windows native wheels use Visual Studio.
- Expanded CI and release matrices to Python 3.14.

## No-Change Areas

No CLI commands, DI APIs, routing decorators, middleware contracts, ORM APIs, auth/session APIs, deployment generators, or public configuration fields changed in b5.
