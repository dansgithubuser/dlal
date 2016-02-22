include(../../../build/CMakeCommon.txt)

option(TEST "ON to test, OFF otherwise")

if(TEST)
	set(src "../src/test.cpp")
endif()

standard_component(Vst)
