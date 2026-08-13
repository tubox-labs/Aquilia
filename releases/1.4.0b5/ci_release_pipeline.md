# CI and Release Pipeline — v1.4.0b5

## Design Goal

A green workflow must prove the artifact users install works, not merely that source code in the checkout can import.

## Wheel Matrix

| Platform | Architecture | CPython |
|---|---|---|
| Linux | x86_64 | 3.10–3.14 |
| Linux | aarch64 | 3.10–3.14 |
| macOS | x86_64 | 3.10–3.14 |
| macOS | arm64 | 3.10–3.14 |
| Windows | AMD64 | 3.10–3.14 |

Free-threaded/no-GIL and 32-bit Windows builds remain excluded.

## Strict Native Wheel Check

`CMAKE_ARGS=-DAQUILIA_ENGINE_OPTIONAL=OFF` overrides the end-user default. The build fails if any extension cannot compile.

After installation, `tools/check_installed_native.py`:

1. changes to a temporary directory;
2. removes the repository root from `sys.path`;
3. imports the installed `aquilia` package;
4. asserts all three native flags;
5. reports the package path and loader diagnostics on failure.

## Compiler-Free Source Check

Windows Python 3.14 CI builds an sdist, sets `CC` and `CXX` to nonexistent paths, installs the archive, changes outside the checkout, and asserts all three native flags are false. This verifies the fallback path instead of the native path.

## Release Gate

The release workflow refuses to proceed unless Windows AMD64 wheels exist for `cp310`, `cp311`, `cp312`, `cp313`, and `cp314`. Build, TestPyPI smoke tests, and production publication depend on the compiler-free sdist check and distribution verification.

## Why Separate Tests Matter

| Test | Expected outcome |
|---|---|
| Binary wheel | all native extensions load |
| Compiler-free sdist | package installs; fallbacks load |
| Editable native build | selected extension tests run natively |
| Python fallback suite | behavior remains compatible without extensions |

Combining these expectations would either reject the supported fallback or permit broken release wheels.

## CI Migration

Custom packagers should replace a plain environment variable such as `AQUILIA_ENGINE_OPTIONAL=OFF` with a CMake definition:

```bash
CMAKE_ARGS="-DAQUILIA_ENGINE_OPTIONAL=OFF" python -m build
```

The plain environment variable does not override `tool.scikit-build.cmake.define.AQUILIA_ENGINE_OPTIONAL` in `pyproject.toml`.

See [Native Wheels and Source Builds](native_packaging.md).
