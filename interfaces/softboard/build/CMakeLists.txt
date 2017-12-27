include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps"
)

#=====source=====#
set(src "${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp")

#=====products=====#
set(output Softboard)
footer(${output} "executable")

#=====linking=====#
danssfml()
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)
