include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
)

#=====source=====#
set(src
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/editor.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/connection.cpp"
)

#=====products=====#
footer(Editor)

#=====linking=====#
set(DANS_SFML_WRAPPER_NO_MODULE ON)
set(DANS_SFML_WRAPPER_STATIC ON)
add_subdirectory(../../../deps/danssfml/wrapper DansSfmlWrapper)
target_link_libraries(Editor DansSfmlWrapperStatic)
