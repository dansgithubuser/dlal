include(../../../build/CMakeCommon.txt)

#=====constants=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(sfmlDir "${CMAKE_CURRENT_SOURCE_DIR}/../../deps/SFML-2.2")
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(sfmlDir "${CMAKE_CURRENT_SOURCE_DIR}/../../deps/SFML-2.2-windows-vc12-32-bit")
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
	set(sfmlDir "${CMAKE_CURRENT_SOURCE_DIR}/../../deps/SFML-2.3-osx-clang-universal")
endif()

set(sfmlSystem sfml-system)
set(sfmlWindow sfml-window)
set(sfmlGraphics sfml-graphics)

if(CMAKE_SYSTEM_NAME MATCHES "Windows" AND CMAKE_BUILD_TYPE MATCHES "Debug")
	set(sfmlSystem sfml-system-d)
	set(sfmlWindow sfml-window-d)
	set(sfmlGraphics sfml-graphics-d)
endif()

#=====include=====#
include_directories(
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../deps"
	"${sfmlDir}/include"
)

#=====source=====#
set(
	src
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/main.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../src/viewer.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/src/skeleton.cpp"
	"${CMAKE_CURRENT_SOURCE_DIR}/../../../skeleton/deps/dyad/src/dyad.c"
)

#=====products=====#
set(output Viewer)
add_executable(${output} ${src})

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(
		sfmlDlls
		"${sfmlDir}/bin/${sfmlGraphics}-2.dll"
		"${sfmlDir}/bin/${sfmlSystem}-2.dll"
		"${sfmlDir}/bin/${sfmlWindow}-2.dll"
	)
	file(COPY ${sfmlDlls} DESTINATION "${CMAKE_BINARY_DIR}")
endif()

#=====linking=====#
find_library(SFML_SYSTEM   ${sfmlSystem}   PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)
find_library(SFML_WINDOW   ${sfmlWindow}   PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)
find_library(SFML_GRAPHICS ${sfmlGraphics} PATHS "${sfmlDir}/lib" NO_DEFAULT_PATH)

target_link_libraries(
	${output}
	${SFML_SYSTEM}
	${SFML_WINDOW}
	${SFML_GRAPHICS}
)

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()

cpp11WithExceptions()
