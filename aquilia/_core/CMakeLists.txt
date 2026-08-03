cmake_minimum_required(VERSION 3.21)
project(aquilia_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
# AQUILIA_SANITIZE: comma-separated -fsanitize list (e.g. "address,undefined").
# Applied to the C++ unit tests only -- never to the wheel extension, which
# must stay ABI-clean for the interpreter that loads it.
set(AQUILIA_SANITIZE "" CACHE STRING "Sanitizers for the C++ unit tests")
option(AQUILIA_ENGINE_TESTS "Build the C++ unit tests" OFF)
# When ON, a missing nanobind degrades to a pure-Python install instead of
# failing it. The wheel is then built without _core and _core_loader falls back.
option(AQUILIA_ENGINE_OPTIONAL "Skip the extension if its deps are unavailable" OFF)

# ---------------------------------------------------------------------------
# The extension
# ---------------------------------------------------------------------------
find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)

if(AQUILIA_ENGINE_OPTIONAL)
  find_package(nanobind CONFIG QUIET)
  if(NOT nanobind_FOUND)
    message(WARNING
      "nanobind not found -- building aquilia WITHOUT the native core engine. "
      "The pure-Python fallback in aquilia/_core_loader.py will be used.")
    return()
  endif()
else()
  find_package(nanobind CONFIG REQUIRED)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# No STABLE_ABI: docs/engine/06-python-binding-architecture.md section 7 rejects
# the limited ABI outright -- the hot path needs PyUnicode_AsUTF8AndSize and
# direct PyLong construction, neither of which it exposes. The wheel matrix is
# per-interpreter and cibuildwheel handles that mechanically.
nanobind_add_module(_core
  NB_STATIC
  src/interner.cpp
  src/router.cpp
  src/request_ctx.cpp
  src/module.cpp
)
target_include_directories(_core PRIVATE src)

if(NOT MSVC)
  target_compile_options(_core PRIVATE -fvisibility=hidden -Wall -Wextra)
endif()

install(TARGETS _core LIBRARY DESTINATION aquilia)

# ---------------------------------------------------------------------------
# C++ unit tests (Phase 9C)
# ---------------------------------------------------------------------------
# Deliberately NOT GoogleTest-via-FetchContent: that needs network at configure
# time, and the assertion harness in tests/harness.hpp is 40 lines. Nothing in
# these tests needs fixtures, mocks, or death tests.
if(AQUILIA_ENGINE_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
