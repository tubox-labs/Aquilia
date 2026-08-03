# C++ unit tests. Built only when AQUILIA_ENGINE_TESTS=ON; never part of the wheel.
#
# These link the core sources directly rather than the nanobind extension:
# interner.cpp and router.cpp include no Python headers, so the trie and string
# table are testable, and sanitizable, without an interpreter in the process.

set(AQ_TEST_SOURCES
  ../src/interner.cpp
  ../src/router.cpp
)

function(aq_add_test name)
  add_executable(${name} ${name}.cpp ${AQ_TEST_SOURCES})
  target_include_directories(${name} PRIVATE ../src .)
  target_compile_features(${name} PRIVATE cxx_std_20)
  if(NOT MSVC)
    target_compile_options(${name} PRIVATE -Wall -Wextra -Wpedantic -g)
  endif()
  if(AQUILIA_SANITIZE)
    target_compile_options(${name} PRIVATE -fsanitize=${AQUILIA_SANITIZE} -fno-omit-frame-pointer)
    target_link_options(${name} PRIVATE -fsanitize=${AQUILIA_SANITIZE})
  endif()
  add_test(NAME ${name} COMMAND ${name})
endfunction()

aq_add_test(test_interner)
aq_add_test(test_router)
