cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

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
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
	add_definitions(-D__MACOSX_CORE__)
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
set(output Midi)
add_library(${output} MODULE ${src})

#=====link=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	target_link_libraries(${output} asound pthread)
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} winmm)
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
	find_library(coreMidi CoreMIDI)
	find_library(coreAudio CoreAudio)
	find_library(coreFoundation CoreFoundation)
	target_link_libraries(${output} ${coreMidi} ${coreAudio} ${coreFoundation})
endif()

#=====c++ standard=====#
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
