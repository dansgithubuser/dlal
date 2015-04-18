cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

option(TEST "ON to test, OFF otherwise")

#=====constants=====#
set(output Sfml)
set(sfmlDir "../deps/SFML-2.2")

#=====include=====#
include_directories(
		"../../../skeleton/src"
		"../src"
		"${sfmlDir}/include"
)

#=====source=====#
set(
	src
	"../src/sfml.cpp"
	"../../../skeleton/src/midiMessages.cpp"
)

if(${TEST})
	set(src ${src} "../src/test.cpp")
endif()

#=====products=====#
if(TEST)
	add_executable(${output} ${src})
else()
	add_library(${output} ${src})
endif()

#=====linking=====#
set(CMAKE_LIBRARY_PATH "${sfmlDir}/lib")

find_library(SFML_SYSTEM sfml-system)
find_library(SFML_WINDOW sfml-window)
find_library(SFML_GRAPHICS sfml-graphics)
find_library(SFML_NETWORK sfml-network)

target_link_libraries(
	${output}
	${SFML_SYSTEM}
	${SFML_WINDOW}
	${SFML_GRAPHICS}
	${SFML_NETWORK}
)

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()
