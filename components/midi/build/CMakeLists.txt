cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
		"../deps/rtmidi"
)

#=====definitions=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	add_definitions(-D__LINUX_ALSA__)
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	add_definitions(-D__WINDOWS_MM__)
endif()

#=====source=====#
set(
	src
	"../src/midi.cpp"
	"../../../skeleton/src/skeleton.cpp"
	"../../../skeleton/src/midiMessages.cpp"
	"../deps/rtmidi/RtMidi.cpp"
)

#=====products=====#
add_library(Midi ${src})

#=====link=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	target_link_libraries(Midi asound pthread)
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(Midi winmm)
endif()

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
