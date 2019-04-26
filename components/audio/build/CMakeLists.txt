cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)

include(../../../build/CMakeCommon.txt)

option(DLAL_TEST "ON to test, OFF otherwise")

if(APPLE)
	set(AUDIO_OSX_CORE ON CACHE BOOL "use osx core")
elseif(WIN32)
	set(AUDIO_WINDOWS_WASAPI ON CACHE BOOL "use windows wasapi")
elseif("${CMAKE_SYSTEM_NAME}" STREQUAL "Linux")
	set(AUDIO_LINUX_ALSA ON CACHE BOOL "use linux alsa")
endif()

set(BUILD_TESTING OFF CACHE BOOL "don't build tests")

add_subdirectory(../deps/rtaudio rtaudio)
get_directory_property(LINKLIBS DIRECTORY ../deps/rtaudio DEFINITION LINKLIBS)

include_directories("../deps/rtaudio")

if(DLAL_TEST)
	add_definitions(-DDLAL_AUDIO_TEST)
endif()

set(output Audio)

if(DLAL_TEST)
	set(src ${src} "../src/test.cpp")
endif()

standard_component(${output})

target_link_libraries(${output} rtaudio_static ${LINKLIBS})
