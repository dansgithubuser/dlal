cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)
cmake_policy(SET CMP0042 NEW)

option(TEST "ON to test, OFF otherwise")

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(ASIO ON)
else()
	set(ASIO OFF)
endif()

#=====include=====#
include_directories(
	"../deps/portaudio/include"
	"../../../skeleton/src"
	"../src"
)

if(ASIO)
	include_directories(
		"../deps/portaudio/src/common"
		"../deps/ASIOSDK2/common"
		"../deps/ASIOSDK2/host"
	)

	if(CMAKE_SYSTEM_NAME MATCHES "Windows")
		include_directories(
			"../deps/portaudio/src/os/win"
			"../deps/ASIOSDK2/host/pc"
		)
	endif()
endif()

#=====defines=====#
if(ASIO)
	add_definitions(-DPA_USE_ASIO=1)
endif()

if(TEST)
	add_definitions(-DTEST_AUDIO)
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	add_definitions(-D_SCL_SECURE_NO_WARNINGS -D_CRT_SECURE_NO_WARNINGS)
endif()

#=====source=====#
set(src "../src/audio.cpp" "../../../skeleton/src/skeleton.cpp")
if(TEST)
	set(src ${src} "../src/test.cpp")
endif()

if(ASIO)
	set(
		src_asio
		"../deps/ASIOSDK2/common/asio.cpp"
		"../deps/ASIOSDK2/host/asiodrivers.cpp"
		"../deps/ASIOSDK2/host/pc/asiolist.cpp"
	)

	set(
		src_pa
		"../deps/portaudio/src/hostapi/asio/pa_asio.cpp"
		"../deps/portaudio/src/common/pa_allocation.c"
		"../deps/portaudio/src/common/pa_converters.c"
		"../deps/portaudio/src/common/pa_cpuload.c"
		"../deps/portaudio/src/common/pa_dither.c"
		"../deps/portaudio/src/common/pa_front.c"
		"../deps/portaudio/src/common/pa_process.c"
		"../deps/portaudio/src/common/pa_ringbuffer.c"
		"../deps/portaudio/src/common/pa_stream.c"
		"../deps/portaudio/src/common/pa_trace.c"
	)

	if(CMAKE_SYSTEM_NAME MATCHES "Windows")
		set(
			src_pa
			${src_pa}
			"../deps/portaudio/src/os/win/pa_win_coinitialize.c"
			"../deps/portaudio/src/os/win/pa_win_hostapis.c"
			"../deps/portaudio/src/os/win/pa_win_util.c"
			"../deps/portaudio/src/os/win/pa_win_waveformat.c"
			"../deps/portaudio/src/os/win/pa_x86_plain_converters.c"
		)
	endif()

	set(src ${src} ${src_pa} ${src_asio})
endif()

#=====products=====#
set(output Audio)
if(TEST)
	add_executable(${output} ${src})
else()
	add_library(${output} MODULE ${src})
endif()

#====linking=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux|Darwin")
	find_library(portaudio portaudio)
	target_link_libraries(${output} ${portaudio})
endif()

#=====c++ standard=====#
set_property(TARGET ${output} PROPERTY CXX_STANDARD 11)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")
endif()
