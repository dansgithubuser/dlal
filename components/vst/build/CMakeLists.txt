include(../../../build/CMakeCommon.txt)

option(DLAL_TEST "ON to test, OFF otherwise")

set(BUILD_SHARED_LIBS_OUTER "${BUILD_SHARED_LIBS}")
set(BUILD_SHARED_LIBS OFF)
if(NOT APPLE AND NOT WIN32 AND CMAKE_COMPILER_IS_GNUCC)
	set(CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS} -fPIC)
endif()
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/SFML" "${CMAKE_CURRENT_BINARY_DIR}/SFML")
set(BUILD_SHARED_LIBS "${BUILD_SHARED_LIBS_OUTER}")

include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/SFML/include")

add_definitions(-DSFML_STATIC)

if(DLAL_TEST)
	set(src "../src/test.cpp")
	add_definitions(-DDLAL_VST_TEST)
endif()

standard_component(Vst)

if(APPLE)
	set_source_files_properties("../src/vst.cpp" APPEND_STRING PROPERTY COMPILE_FLAGS "-x objective-c++ -fobjc-arc")
endif()

target_link_libraries(Vst sfml-system sfml-window)
