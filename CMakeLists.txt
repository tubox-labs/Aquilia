# Parent project for aquilia's native extensions.
#
# Exists because there are now two: _core (request path -- router, request
# context) and _dataengine (data path -- row and field plans). scikit-build-core
# takes a single cmake.source-dir, so that directory has to be a project that
# owns both rather than one of the extensions themselves.
#
# Each subdirectory keeps its own project() and find_package() calls, so
# `cmake -S aquilia/_core` still configures standalone. The sanitizer CI jobs
# rely on that, and keeping it true means neither extension's build can break
# the other's.
cmake_minimum_required(VERSION 3.21)
project(aquilia_native LANGUAGES CXX)

# Declared here as well as in the subdirectories so a -D flag passed to this
# project reaches both. CACHE variables are idempotent, so the subdirectory
# declarations become harmless no-ops.
set(AQUILIA_SANITIZE "" CACHE STRING "Sanitizers for the C++ unit tests")
option(AQUILIA_ENGINE_TESTS "Build the C++ unit tests" OFF)
option(AQUILIA_ENGINE_OPTIONAL "Skip an extension if its deps are unavailable" OFF)

if(AQUILIA_ENGINE_TESTS)
  enable_testing()
endif()

add_subdirectory(aquilia/_core)
add_subdirectory(aquilia/_dataengine)
