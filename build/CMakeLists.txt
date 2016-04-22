include(CMakeCommon.txt)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR})

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR})

sfml()

add_subdirectory(../skeleton/build skeleton)

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
