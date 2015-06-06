cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

file(GLOB src "../src/skeleton.cpp" "../src/midiMessages.cpp")

add_library(Skeleton ${src})

if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
