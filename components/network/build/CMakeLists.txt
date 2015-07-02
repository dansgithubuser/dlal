include(../../../build/CMakeCommon.txt)

set(output Network)

include_directories("../../../skeleton/deps/dyad/src")

set(src "../../../skeleton/deps/dyad/src/dyad.c" )
if(TEST)
	set(src ${src} "../src/test.cpp")
	add_definitions(-DTEST)
endif()
component_src(page)

footer()
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
	target_link_libraries(${output} ws2_32)
endif()
