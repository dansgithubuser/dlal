cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

file(GLOB src "../src/skeleton.cpp")

add_library(Skeleton ${src})

if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()
