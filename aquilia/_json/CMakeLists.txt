cmake_minimum_required(VERSION 3.21)
project(aquilia_json LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 11)

# ---------------------------------------------------------------------------
# Options -- mirror aquilia/_core and aquilia/_dataengine so each extension
# configures standalone. The sanitizer CI jobs rely on that.
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
      "nanobind not found -- building aquilia WITHOUT the native JSON engine. "
      "aquilia/json.py falls back to the standard library.")
    return()
  endif()
else()
  find_package(nanobind CONFIG REQUIRED)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# yyjson is vendored rather than found: it is a single .c/.h pair with no build
# system of its own, and pinning the exact source we ship removes any chance of
# a distro build picking up a version whose number formatting differs. See
# vendor/yyjson/LICENSE (MIT).
add_library(aquilia_yyjson STATIC vendor/yyjson/yyjson.c src/yyjson_dtoa.c)
target_include_directories(aquilia_yyjson PUBLIC vendor/yyjson src)
set_target_properties(aquilia_yyjson PROPERTIES POSITION_INDEPENDENT_CODE ON)
if(NOT MSVC)
  # -O2 explicitly: the parser and the double formatter are the whole point of
  # the dependency, and a debug-configured build would make the extension
  # slower than the stdlib.
  target_compile_options(aquilia_yyjson PRIVATE -O2 -fvisibility=hidden)
endif()

# No STABLE_ABI, for the same reason _core and _dataengine reject it: the hot
# paths need PyUnicode_AsUTF8AndSize and direct PyLong/PyDict/PyList
# construction, none of which the limited ABI exposes.
nanobind_add_module(_json
  NB_STATIC
  src/encode.cpp
  src/decode.cpp
  src/module.cpp
)
target_include_directories(_json PRIVATE src)
target_link_libraries(_json PRIVATE aquilia_yyjson)

if(NOT MSVC)
  target_compile_options(_json PRIVATE -fvisibility=hidden -Wall -Wextra)
endif()

install(TARGETS _json LIBRARY DESTINATION aquilia)

# ---------------------------------------------------------------------------
# C++ unit tests
# ---------------------------------------------------------------------------
if(AQUILIA_ENGINE_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
