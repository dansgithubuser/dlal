cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)
include(CMakeCommon.txt)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR})

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR})

set(CMAKE_INSTALL_PREFIX ${CMAKE_BINARY_DIR}/installed)

danssfml()

add_subdirectory(../skeleton/build skeleton)
add_subdirectory(../deps/danssfml/wrapper dans-sfml-wrapper)

file(GLOB components ../components/*)
foreach(i ${components})
	get_filename_component(bin "${i}" NAME)
	add_subdirectory("${i}/build" "${bin}_bin")
endforeach()

file(GLOB interfaces ../interfaces/*)
foreach(i ${interfaces})
	get_filename_component(bin "${i}" NAME)
	if(NOT bin MATCHES "deps")
		add_subdirectory("${i}/build" "${bin}_bin")
	endif()
endforeach()
