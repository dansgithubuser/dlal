include(../../../build/CMakeCommon.txt)
standard_component(Buffer)
danssfml()
target_link_libraries(Buffer sfml-system sfml-audio)
