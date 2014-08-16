cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

option(ASIO "ON to use ASIO, OFF otherwise")
option(TEST "ON to test, OFF otherwise")

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
			"../deps/portaudio/src/os/win/pa_win_hostapis.c"
			"../deps/portaudio/src/os/win/pa_win_util.c"
			"../deps/portaudio/src/os/win/pa_win_waveformat.c"
			"../deps/portaudio/src/os/win/pa_x86_plain_converters.c"
		)
	endif()

	set(src ${src} ${src_pa} ${src_asio})
endif()

#=====products=====#
if(TEST)
	add_executable(Audio ${src})
else()
	add_library(Audio ${src})
endif()

#====linking=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	target_link_libraries(Audio portaudio)
endif()

#=====c++ standard=====#
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
	set(CMAKE_CXX_FLAGS "-std=c++11")
endif()

