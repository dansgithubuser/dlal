include(../../../build/CMakeCommon.txt)

#=====source=====#
set(src
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/viewer.cpp"
)

#=====products=====#
set(output Viewer)
footer(${output} "executable")

#=====linking=====#
danssfml()
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)
