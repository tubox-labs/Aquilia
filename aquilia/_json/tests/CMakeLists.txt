# C++ unit tests for the JSON engine. Built only when AQUILIA_ENGINE_TESTS=ON;
# never part of the wheel.
#
# Only escape.hpp and buffer.hpp are covered here, and deliberately so: they
# include no Python headers, so the escape scanner and the buffer pool are
# testable -- and sanitizable -- without an interpreter in the process. That
# matters, because the escape scanner is word-at-a-time bit arithmetic where a
# subtly wrong identity passes an ASCII spot-check and corrupts non-ASCII output.
#
# encode.cpp and decode.cpp touch CPython, so they are covered by the Python
# parity and fuzz tests in tests/json/ instead, where an interpreter exists by
# construction.

function(aq_add_json_test name)
  add_executable(${name} ${name}.cpp)
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

aq_add_json_test(test_escape)
aq_add_json_test(test_buffer)
