include(../../../build/CMakeCommon.txt)

option(TEST "ON to test, OFF otherwise")

set(BUILD_SHARED_LIBS_OUTER "${BUILD_SHARED_LIBS}")
set(BUILD_SHARED_LIBS OFF)
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/SFML" "${CMAKE_CURRENT_BINARY_DIR}/SFML")
set(BUILD_SHARED_LIBS "${BUILD_SHARED_LIBS_OUTER}")

include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/SFML/include")

add_definitions(-DSFML_STATIC)

if(TEST)
	set(src "../src/test.cpp")
	add_definitions(-DDLAL_VST_TEST)
endif()

standard_component(Vst)

target_link_libraries(Vst sfml-system sfml-window)
