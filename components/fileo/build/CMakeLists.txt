cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
)

#=====source=====#
set(src
	"../src/fileo.cpp"
	"../../../skeleton/src/skeleton.cpp"
	"../../../skeleton/src/midiMessages.cpp"
	"../../../skeleton/src/page.cpp"
)

#=====products=====#
add_library(Fileo ${src})

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
