include(../../../build/CMakeCommon.txt)
standard_component(Filea)
sfml()
target_link_libraries(Filea sfml-system sfml-audio)
