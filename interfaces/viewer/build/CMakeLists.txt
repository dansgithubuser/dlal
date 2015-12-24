include(../../../build/CMakeCommon.txt)

#=====subdirectories=====#
set(BUILD_SHARED_LIBS OFF CACHE BOOL "static")
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../../deps/SFML" "${CMAKE_CURRENT_BINARY_DIR}/SFML")

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps/SFML/include"
)

#=====defines=====#
add_definitions(-DSFML_STATIC)

#=====source=====#
set(
	src
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/viewer.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src/skeleton.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src/dyad.c"
)

#=====products=====#
set(output Viewer)
add_executable(${output} ${src})

#=====linking=====#
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()

cpp11WithExceptions()
