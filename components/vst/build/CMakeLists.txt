include(../../../build/CMakeCommon.txt)

option(TEST "ON to test, OFF otherwise")

if(TEST)
	set(src "../src/test.cpp")
	add_definitions(-DDLAL_VST_TEST)
endif()

standard_component(Vst)
