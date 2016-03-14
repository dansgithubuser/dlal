include(../../../build/CMakeCommon.txt)

option(TEST "ON to test, OFF otherwise")

add_definitions(-DPA_WDMKS_NO_KSGUID_LIB)

add_subdirectory("../deps/portaudio" "${CMAKE_CURRENT_BINARY_DIR}/portaudio")

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

target_link_libraries(${output} portaudio_static)
