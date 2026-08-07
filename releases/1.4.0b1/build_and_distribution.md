# Build & Distribution — v1.4.0b1

To accommodate the three new C++ native extensions (`_core`, `_dataengine`, `_json`) while maintaining the ease of installation Python developers expect, Aquilia v1.4.0b1 entirely overhauls its build and distribution pipeline.

## Build Backend: `scikit-build-core`

We have replaced `setuptools` with `scikit-build-core` as the `build-backend` in `pyproject.toml`. 

Why `scikit-build-core`?
1. **Modern CMake Integration:** It natively hooks into CMake, allowing us to manage C++ compilation independent of Python's legacy distutils.
2. **Dynamic Metadata:** It extracts `metadata.version` directly from the `aquilia/__init__.py` regex, maintaining a single source of truth.
3. **Sdist Management:** Precise include/exclude rules guarantee clean source distributions without packaging massive C++ object files or git artifacts.

### `pyproject.toml` Changes
```toml
[build-system]
requires = ["scikit-build-core>=0.8.0", "nanobind>=1.9.0"]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
wheel.expand-macos-universal-tags = true
sdist.include = ["src/aquilia/engines/*", "CMakeLists.txt"]
sdist.exclude = [".git*", "docs/", "tests/"]
metadata.version.provider = "scikit_build_core.metadata.regex"
metadata.version.input = "aquilia/__init__.py"
```

## CMake and Nanobind

Aquilia uses `nanobind` (the modern successor to `pybind11`) to expose C++ structures to Python. It produces smaller, faster binaries.

### CMake Structure
The root `CMakeLists.txt` orchestrates the build. It requires CMake 3.15+.

```cmake
cmake_minimum_required(VERSION 3.15...3.27)
project(aquilia_engines LANGUAGES CXX)

find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(nanobind CONFIG REQUIRED)

# Submodules
add_subdirectory(aquilia/_core/src)
add_subdirectory(aquilia/_dataengine/src)
add_subdirectory(aquilia/_json/src)
```

Each extension has its own local `CMakeLists.txt` that utilizes `nanobind_add_module()`:

```cmake
# aquilia/_json/src/CMakeLists.txt
nanobind_add_module(_json decode.cpp encode.cpp)
target_compile_options(_json PRIVATE -O3 -flto)
```

## GitHub Actions: `cibuildwheel`

The most critical part of distributing C++ Python packages is providing pre-compiled wheels, so end-users do not need a C++ compiler. 

We introduced a dedicated `.github/workflows/wheels.yml` pipeline powered by `cibuildwheel`.

**Supported Matrix:**
- **OS:** `ubuntu-latest`, `macos-14` (Apple Silicon), `macos-13` (Intel), `windows-latest`
- **Architectures:** 
  - Linux: `x86_64`, `aarch64` (via QEMU)
  - macOS: `x86_64`, `arm64`
  - Windows: `AMD64`
- **Python Versions:** 3.10, 3.11, 3.12, 3.13

### Test Configuration in CI
`cibuildwheel` is configured to run the pytest suite against the compiled wheel *before* uploading it.
```toml
[tool.cibuildwheel]
test-command = "pytest {project}/tests -m 'not slow'"
test-requires = "pytest"
```

## How to Install

### Installing Pre-Built Wheels (Default)
Simply run:
```bash
pip install aquilia==1.4.0b1
```
`pip` will fetch the binary wheel for your OS and architecture. Installation takes ~2 seconds. No compiler required.

### Building from Source (Fallback / Development)
If you are on an exotic architecture (e.g., FreeBSD, Alpine/musl without a wheel, or a Raspberry Pi), pip will download the Source Distribution (`sdist`) and attempt to compile it locally.

**Requirements:**
- A C++17 compliant compiler (GCC 9+, Clang 10+, MSVC 2019+).
- CMake 3.15+.
- Python development headers (`python3-dev`).

### Forcing a Pure-Python Install
Aquilia guarantees a fail-soft pure Python architecture. If you cannot or do not want to compile the C++ extensions, use the `AQUILIA_ENGINE_OPTIONAL` flag.

```bash
export AQUILIA_ENGINE_OPTIONAL=ON
pip install aquilia==1.4.0b1 --no-binary aquilia
```
The build system detects this environment variable, skips the CMake compilation step, and packages the Python source files. When Aquilia boots, the `_loader.py` files will gracefully fall back to the Python standard library equivalents.
