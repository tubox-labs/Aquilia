# Native Wheels and Source Builds — v1.4.0b5

## Overview

Aquilia contains three optional native extensions: `_core`, `_dataengine`, and `_json`. They accelerate framework internals but do not define a separate public API edition. v1.4.0b5 repairs both distribution modes: strict binary wheels and optional source builds.

## Previous Behavior

### Windows wheel imports

A wheel built successfully on GitHub Actions, installed successfully with pip, and still failed at import:

```text
DLL load failed while importing _dataengine: The specified module could not be found.
```

The same runner contained the required preview MSVC runtime, so checkout-based tests did not reproduce a clean user machine.

### Compiler-free source installs

The root build declared:

```cmake
project(aquilia_native LANGUAGES C CXX)
```

CMake aborted there when no compiler existed. `AQUILIA_ENGINE_OPTIONAL=ON` was processed later, making the fallback branch unreachable.

## New Build Architecture

```text
scikit-build-core
  -> CMake project(LANGUAGES NONE)
      -> check_language(C/CXX)
          -> compilers found: enable languages and build all extensions
          -> missing compiler + OPTIONAL=ON: return and package Python fallbacks
          -> missing compiler + OPTIONAL=OFF: fail the build
```

This keeps end-user installation resilient while making release artifacts strict.

## Windows ABI and Runtime

Release wheel jobs use:

```text
Runner: windows-2022
Generator: Visual Studio 17 2022
Architecture: AMD64
Runtime: MultiThreaded / MultiThreadedDebug (static)
```

The runtime setting is applied at the root and in each extension CMake file so standalone sanitizer/test builds receive the same property.

## Installation Examples

### Published wheel

```bash
python -m pip install "aquilia==1.4.0b5"
```

### Optional source install

```bash
python -m pip install --no-binary aquilia "aquilia==1.4.0b5"
```

Without a compiler, this succeeds with Python fallbacks. Ninja is supplied as a build requirement so CMake can run its probe without depending on NMake.

### Strict source build

```bash
CMAKE_ARGS="-DAQUILIA_ENGINE_OPTIONAL=OFF" python -m pip install .
```

Use strict mode in extension development and packaging CI. A missing compiler or dependency is an error.

## Verification

```bash
python -c "from aquilia._core_loader import NATIVE, engine_info; from aquilia._dataengine_loader import DATAENGINE_NATIVE, dataengine_info; from aquilia.json import native as JSON_NATIVE; print(NATIVE, engine_info()); print(DATAENGINE_NATIVE, dataengine_info()); print(JSON_NATIVE)"
```

Expected for a release wheel: all native flags are `True`.

Expected for a compiler-free source install: all native flags may be `False`, with diagnostic reasons explaining that the modules are unavailable.

## Compatibility and Edge Cases

- Wheels are specific to CPython minor version, OS, and architecture.
- `AQUILIA_ENGINE=0` and `AQUILIA_DATAENGINE=0` disable loading at runtime; they do not change what a wheel contains.
- A source checkout can shadow an installed package. Change to a temporary directory before testing an installed wheel.
- The Windows error message does not name the missing dependent DLL. Use b5 or newer before investigating system redistributables.
- Static MSVC linkage increases extension binary size slightly but removes the fragile external runtime dependency.

## Related Documentation

- [Installation guide](../../aqdocx/src/pages/docs/getting-started/Installation.tsx)
- [CI and Release Pipeline](ci_release_pipeline.md)
- [Migration Guide](migration.md)
