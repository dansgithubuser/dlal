include(../../../build/CMakeCommon.txt)

#=====include=====#
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../deps")

#=====source=====#
set(src "${CMAKE_CURRENT_SOURCE_DIR}/../src/sfml.cpp")

#=====products=====#
set(output Sfml)
add_library(${output} MODULE ${src})
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)

#=====linking=====#
sfml()
target_link_libraries(${output} sfml-system sfml-window sfml-graphics)
