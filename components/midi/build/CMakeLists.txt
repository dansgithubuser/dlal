cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
		"../deps/rtmidi"
)

#=====source=====#
set(
	src
	"../src/midi.cpp"
	"../../../skeleton/src/skeleton.cpp"
	"../deps/rtmidi/RtMidi.cpp"
)

#=====products=====#
add_library(Midi ${src})

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()
