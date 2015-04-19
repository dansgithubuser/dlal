cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
)

#=====source=====#
set(src "../src/multiplier.cpp" "../../../skeleton/src/skeleton.cpp")

#=====products=====#
add_library(Multiplier ${src})

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()
