cmake_minimum_required(VERSION 2.8.12.2 FATAL_ERROR)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_subdirectory(../skeleton/build skeleton)

function(add_components)
  foreach(component ${ARGV})
    add_subdirectory("../components/${component}/build" ${component})
  endforeach()
endfunction()

add_components(
  audio
  fm
  midi
  sfml
)
