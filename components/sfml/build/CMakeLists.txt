cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

option(TEST "ON to test, OFF otherwise")

#=====constants=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(sfmlDir "../deps/SFML-2.2")
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(sfmlDir "../deps/SFML-2.2-windows-vc12-32-bit")
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
	set(sfmlDir "../deps/SFML-2.3-osx-clang-universal")
endif()

set(sfmlSystem sfml-system)
set(sfmlWindow sfml-window)
set(sfmlGraphics sfml-graphics)
set(sfmlNetwork sfml-network)

if(CMAKE_SYSTEM_NAME MATCHES "Windows" AND CMAKE_BUILD_TYPE MATCHES "Debug")
	set(sfmlSystem sfml-system-d)
	set(sfmlWindow sfml-window-d)
	set(sfmlGraphics sfml-graphics-d)
	set(sfmlNetwork sfml-network-d)
endif()

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
	"../../../skeleton/src/skeleton.cpp"
	"../../../skeleton/src/midiMessages.cpp"
)

if(${TEST})
	set(src ${src} "../src/test.cpp")
endif()

#=====products=====#
set(output Sfml)
if(TEST)
	add_executable(${output} ${src})
else()
	add_library(${output} MODULE ${src})
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(
		sfmlDlls
		"${sfmlDir}/bin/${sfmlGraphics}-2.dll"
		"${sfmlDir}/bin/${sfmlNetwork}-2.dll"
		"${sfmlDir}/bin/${sfmlSystem}-2.dll"
		"${sfmlDir}/bin/${sfmlWindow}-2.dll"
	)
	file(COPY ${sfmlDlls} DESTINATION "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}")
endif()

#=====linking=====#
find_library(SFML_SYSTEM   ${sfmlSystem}   PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)
find_library(SFML_WINDOW   ${sfmlWindow}   PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)
find_library(SFML_GRAPHICS ${sfmlGraphics} PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)
find_library(SFML_NETWORK  ${sfmlNetwork}  PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)

target_link_libraries(
	${output}
	${SFML_SYSTEM}
	${SFML_WINDOW}
	${SFML_GRAPHICS}
	${SFML_NETWORK}
)

#=====c++ standard=====#
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
