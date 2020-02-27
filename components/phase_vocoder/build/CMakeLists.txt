cmake_minimum_required(VERSION 3.2.3 FATAL_ERROR)

include(../../../build/CMakeCommon.txt)

set(output PhaseVocoder)

standard_component(${output})

set(rustDir "${CMAKE_CURRENT_SOURCE_DIR}/../rust/phase_vocoder")
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
	add_custom_target(rustPhaseVocoderBuild cargo build           WORKING_DIRECTORY "${rustDir}")
	set(rustBuildType debug)
else()
	add_custom_target(rustPhaseVocoderBuild cargo build --release WORKING_DIRECTORY "${rustDir}")
	set(rustBuildType release)
endif()
add_dependencies(${output} rustPhaseVocoderBuild)
target_link_libraries(${output} "${rustDir}/target/${rustBuildType}/${CMAKE_STATIC_LIBRARY_PREFIX}phase_vocoder${CMAKE_STATIC_LIBRARY_SUFFIX}")
