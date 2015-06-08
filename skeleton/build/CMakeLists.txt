cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

file(GLOB src "../src/skeleton.cpp" "../src/midiMessages.cpp")

set(output Skeleton)
add_library(${output} MODULE ${src})

set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
