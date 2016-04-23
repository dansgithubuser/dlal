include(../../../build/CMakeCommon.txt)

option(DLAL_TEST "ON to test, OFF otherwise")

add_definitions(-DPA_WDMKS_NO_KSGUID_LIB)

if(WIN32)
	add_subdirectory("../deps/portaudio" "${CMAKE_CURRENT_BINARY_DIR}/portaudio")
endif()

include_directories("../deps/portaudio/include")

if(DLAL_TEST)
	add_definitions(-DDLAL_AUDIO_TEST)
endif()

set(output Audio)

if(DLAL_TEST)
	set(src ${src} "../src/test.cpp")
endif()

standard_component(${output})

if(NOT WIN32)
	execute_process(
		COMMAND python portaudio.py
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		RESULT_VARIABLE result
	)
	if(${result})
		message(FATAL_ERROR "portaudio build failed")
	endif()
endif()

if(WIN32)
	target_link_libraries(${output} portaudio_static)
else()
	function(find_and_link target static)
		foreach(i ${ARGN})
			if(static)
				find_library(x NAMES lib${i}.a ${i})
			else()
				find_library(x ${i})
			endif()
			if("${x}" MATCHES "NOTFOUND")
				message(FATAL_ERROR "${i} not found")
			endif()
			target_link_libraries(${target} ${x})
			unset(x CACHE)
		endforeach()
	endfunction()
	set(CMAKE_LIBRARY_PATH ${CMAKE_LIBRARY_PATH} ../deps/portaudio/lib/.libs)
	find_and_link(${output} ON portaudio)
	if(APPLE)
		find_and_link(${output} OFF CoreAudio AudioToolbox AudioUnit CoreServices Carbon)
	else()
		target_link_libraries(${output} jack)
	endif()
endif()
