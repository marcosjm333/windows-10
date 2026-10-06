cmake_minimum_required(VERSION 3.24)
project(windows_10_kernel VERSION 0.1.0 LANGUAGES NONE)
find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
set(NW_CONFIG "CHECKED" CACHE STRING "DEBUG, CHECKED or RELEASE")
set_property(CACHE NW_CONFIG PROPERTY STRINGS DEBUG CHECKED RELEASE)
if(NOT NW_CONFIG MATCHES "^(DEBUG|CHECKED|RELEASE)$")
  message(FATAL_ERROR "NW_CONFIG must be DEBUG, CHECKED or RELEASE")
endif()
add_custom_target(kernel ALL
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/build.py" --config "${NW_CONFIG}" --host
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
add_custom_target(analyze
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/scripts/build.py" --config "${NW_CONFIG}" --analyze
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
enable_testing()
add_test(NAME host_contracts COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/host/test_core.py" --config "${NW_CONFIG}")
set_tests_properties(host_contracts PROPERTIES WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" TIMEOUT 180)
add_custom_target(website
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/website/scripts/build.py"
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
