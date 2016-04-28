include(../../../build/CMakeCommon.txt)

option(DLAL_TEST "ON to test, OFF otherwise")

if(DLAL_TEST)
	set(src "../src/test.cpp")
	add_definitions(-DDLAL_VST_TEST)
endif()

standard_component(Vst)

if(APPLE)
	set_source_files_properties("../src/vst.cpp" APPEND_STRING PROPERTY COMPILE_FLAGS "-x objective-c++ -fobjc-arc")
endif()

sfml()
target_link_libraries(Vst sfml-system sfml-window sfml-graphics)
