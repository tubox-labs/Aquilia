# C++ unit tests for the data engine. Built only when AQUILIA_ENGINE_TESTS=ON;
# never part of the wheel.
#
# These link the engine sources directly rather than the nanobind extension.
# uuid_parse.cpp includes no Python headers, so hex parsing is testable -- and
# sanitizable -- without an interpreter in the process. Sources that do touch
# CPython (convert, fieldplan, rowplan) are covered by the Python parity tests
# in tests/dataengine/ instead, where an interpreter exists by construction.

set(AQ_DATA_TEST_SOURCES
  ../src/uuid_parse.cpp
)

function(aq_add_data_test name)
  add_executable(${name} ${name}.cpp ${AQ_DATA_TEST_SOURCES})
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

aq_add_data_test(test_uuid_parse)
