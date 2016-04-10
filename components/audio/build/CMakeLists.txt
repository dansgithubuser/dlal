include(../../../build/CMakeCommon.txt)

option(TEST "ON to test, OFF otherwise")

add_definitions(-DPA_WDMKS_NO_KSGUID_LIB)

if(WIN32)
	add_subdirectory("../deps/portaudio" "${CMAKE_CURRENT_BINARY_DIR}/portaudio")
endif()

include_directories("../deps/portaudio/include")

if(TEST)
	add_definitions(-DTEST_AUDIO)
endif()

set(output Audio)
component_src()

if(TEST)
	set(src ${src} "../src/test.cpp")
endif()

footer()

if(NOT WIN32)
	add_custom_command(
		TARGET ${output}
		PRE_LINK
		COMMAND ./configure
		COMMAND make
		WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../deps/portaudio"
	)
endif()

if(WIN32)
	target_link_libraries(${output} portaudio_static)
elseif(APPLE)
	function(find_and_link target)
		foreach(i ${ARGN})
			unset(x CACHE)
			find_library(x ${i})
			if("${x}" MATCHES "NOTFOUND")
				message(FATAL_ERROR "${i} not found")
			endif()
			target_link_libraries(${target} ${x})
		endforeach()
	endfunction()
	find_and_link(${output} CoreAudio AudioToolbox AudioUnit CoreServices Carbon portaudio)
endif()
