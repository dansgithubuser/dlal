include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps"
)

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
sfml()
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()

cpp11WithExceptions()
