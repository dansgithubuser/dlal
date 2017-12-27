include(../../../build/CMakeCommon.txt)
standard_component(Filea)
danssfml()
target_link_libraries(Filea sfml-system sfml-audio)
