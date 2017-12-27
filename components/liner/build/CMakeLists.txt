include(../../../build/CMakeCommon.txt)
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/dansmidilibs")
set(src "${CMAKE_CURRENT_SOURCE_DIR}/../../../deps/dansmidilibs/midi.cpp")
standard_component(Liner)
