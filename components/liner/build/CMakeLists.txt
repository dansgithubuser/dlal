include(../../../build/CMakeCommon.txt)
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/midi")
set(src "${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/midi/midi.cpp")
standard_component(Liner)
