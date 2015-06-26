include(../../../build/CMakeCommon.txt)

set(output Network)

include_directories("../../../skeleton/deps/dyad/src")

set(src "../../../skeleton/deps/dyad/src/dyad.c" )
component_src(midiMessages page)

footer()
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()
