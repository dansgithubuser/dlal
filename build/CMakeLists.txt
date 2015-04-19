cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_subdirectory(../skeleton/build skeleton)

file(GLOB components ../components/*)

foreach(component ${components})
	string(REGEX MATCH [^/\\]*$ bin "${component}")
	add_subdirectory("${component}/build" "${bin}")
endforeach()
