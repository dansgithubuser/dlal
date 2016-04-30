include(../../../build/CMakeCommon.txt)
standard_component(Buffer)
sfml()
target_link_libraries(Buffer sfml-system sfml-audio)
