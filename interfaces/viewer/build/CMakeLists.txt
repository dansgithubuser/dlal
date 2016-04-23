include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps"
)

#=====source=====#
set(src
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/viewer.cpp"
)

#=====products=====#
set(output Viewer)
footer(${output} "executable")

#=====linking=====#
sfml()
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)
