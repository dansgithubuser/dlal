cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
)

#=====source=====#
set(
	src
	"../src/liner.cpp"
	"../../../skeleton/src/skeleton.cpp"
	"../../../skeleton/src/midiMessages.cpp"
)

#=====products=====#
set(output Liner)
add_library(${output} MODULE ${src})

#=====c++ standard=====#
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
