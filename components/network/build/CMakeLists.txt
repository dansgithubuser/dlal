cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../../../skeleton/deps/dyad/src"
		"../src"
)

#=====source=====#
set(
	src
	"../src/network.cpp"
	"../../../skeleton/src/skeleton.cpp"
	"../../../skeleton/src/midiMessages.cpp"
	"../../../skeleton/src/page.cpp"
	"../../../skeleton/deps/dyad/src/dyad.c"
)

#=====products=====#
set(output Network)
if(TEST)
	add_executable(${output} ${src} "../src/test.cpp")
else()
	add_library(${output} MODULE ${src})
endif()

#=====linking=====#
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()

#=====c++ standard=====#
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
