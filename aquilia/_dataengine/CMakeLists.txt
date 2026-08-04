cmake_minimum_required(VERSION 3.21)
project(aquilia_dataengine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# Options -- mirror aquilia/_core so either extension configures standalone.
# ---------------------------------------------------------------------------
set(AQUILIA_SANITIZE "" CACHE STRING "Sanitizers for the C++ unit tests")
option(AQUILIA_ENGINE_TESTS "Build the C++ unit tests" OFF)
option(AQUILIA_ENGINE_OPTIONAL "Skip the extension if its deps are unavailable" OFF)

# ---------------------------------------------------------------------------
# The extension
# ---------------------------------------------------------------------------
find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)

if(AQUILIA_ENGINE_OPTIONAL)
  find_package(nanobind CONFIG QUIET)
  if(NOT nanobind_FOUND)
    message(WARNING
      "nanobind not found -- building aquilia WITHOUT the native data engine. "
      "The pure-Python fallback in aquilia/_dataengine_loader.py will be used.")
    return()
  endif()
else()
  find_package(nanobind CONFIG REQUIRED)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# No STABLE_ABI, for the same reason _core rejects it: the hot paths need
# PyUnicode_AsUTF8AndSize and direct PyLong/PyDict construction, none of which
# the limited ABI exposes.
nanobind_add_module(_dataengine
  NB_STATIC
  src/uuid_parse.cpp
  src/convert.cpp
  src/fieldplan.cpp
  src/module.cpp
)
target_include_directories(_dataengine PRIVATE src)

if(NOT MSVC)
  target_compile_options(_dataengine PRIVATE -fvisibility=hidden -Wall -Wextra)
endif()

install(TARGETS _dataengine LIBRARY DESTINATION aquilia)

# ---------------------------------------------------------------------------
# C++ unit tests
# ---------------------------------------------------------------------------
if(AQUILIA_ENGINE_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
