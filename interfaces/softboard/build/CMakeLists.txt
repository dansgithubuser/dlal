include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
)

#=====source=====#
set(src "${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp")

#=====products=====#
footer(Softboard "executable")

#=====linking=====#
danssfml()
target_link_libraries(Softboard sfml-system sfml-window sfml-graphics)
