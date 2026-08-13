# Parent project for aquilia's native extensions.
#
# Exists because there are now three: _core (request path -- router, request
# context), _dataengine (data path -- row and field plans), and _json (the JSON
# codec). scikit-build-core takes a single cmake.source-dir, so that directory
# has to be a project that owns all of them rather than one of the extensions
# themselves.
#
# Each subdirectory keeps its own project() and find_package() calls, so
# `cmake -S aquilia/_core` still configures standalone. The sanitizer CI jobs
# rely on that, and keeping it true means no extension's build can break
# another's.
cmake_minimum_required(VERSION 3.21)

# LANGUAGES NONE, then enable_language() below once a compiler is known to
# exist. `project(... LANGUAGES C CXX)` aborts configure outright when no
# compiler is installed, which made AQUILIA_ENGINE_OPTIONAL unreachable dead
# code: every subdirectory's "degrade to pure Python" branch lives *after* this
# line, so an sdist install on a machine without a toolchain (typically Windows
# with no Visual Studio Build Tools) failed the whole `pip install` instead of
# falling back. Probe first, decide second.
project(aquilia_native LANGUAGES NONE)

# Declared here as well as in the subdirectories so a -D flag passed to this
# project reaches all of them. CACHE variables are idempotent, so the
# subdirectory declarations become harmless no-ops.
set(AQUILIA_SANITIZE "" CACHE STRING "Sanitizers for the C++ unit tests")
option(AQUILIA_ENGINE_TESTS "Build the C++ unit tests" OFF)
option(AQUILIA_ENGINE_OPTIONAL "Skip an extension if its deps are unavailable" OFF)

include(CheckLanguage)
check_language(C)
check_language(CXX)

if(NOT CMAKE_C_COMPILER OR NOT CMAKE_CXX_COMPILER)
  if(AQUILIA_ENGINE_OPTIONAL)
    message(WARNING
      "No C/C++ compiler found -- building aquilia WITHOUT its native "
      "extensions (_core, _dataengine, _json). The package is fully "
      "functional; the pure-Python fallbacks in aquilia/_core_loader.py, "
      "aquilia/_dataengine_loader.py, and aquilia/json.py will be used. "
      "To get the accelerated build, install a C++20 compiler "
      "(Windows: Visual Studio Build Tools; Linux: gcc/g++; macOS: Xcode "
      "command line tools) and reinstall.")
    return()
  endif()
  message(FATAL_ERROR
    "No C/C++ compiler found and AQUILIA_ENGINE_OPTIONAL=OFF. Install a "
    "C++20 compiler, or configure with -DAQUILIA_ENGINE_OPTIONAL=ON to build "
    "the pure-Python package instead.")
endif()

enable_language(C)
enable_language(CXX)

# Binary wheels must load on clean Windows machines, not only on CI runners
# that happen to have the matching Visual C++ Redistributable installed.
# Initialize every target (including nanobind's static support libraries) with
# the static MSVC runtime so the .pyd files do not depend on msvcp/vcruntime
# DLLs from the build host's toolchain generation.
if(MSVC)
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

if(AQUILIA_ENGINE_TESTS)
  enable_testing()
endif()

add_subdirectory(aquilia/_core)
add_subdirectory(aquilia/_dataengine)
add_subdirectory(aquilia/_json)
