include(../../../build/CMakeCommon.txt)

set(simpleFftPath ../deps/Simple-FFT)

include_directories("${simpleFftPath}/include")

standard_component(Fir)
