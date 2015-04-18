cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
)

#=====source=====#
set(src "../src/fm.cpp" "../../../skeleton/src/midiMessages.cpp")

#=====products=====#
add_library(Fm ${src})

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()
