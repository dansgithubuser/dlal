include(../../../build/CMakeCommon.txt)

option(DLAL_TEST "ON to test, OFF otherwise")

set(fluidsynthdir ../deps/fluidsynth)

set(output Soundfont)
component_src()

#=====include=====#
include_directories(
	../src/fake
	${fluidsynthdir}/src
	${fluidsynthdir}/src/synth
	${fluidsynthdir}/src/rvoice
	${fluidsynthdir}/src/midi
	${fluidsynthdir}/src/utils
	${fluidsynthdir}/src/sfloader
	${fluidsynthdir}/src/bindings
	${fluidsynthdir}/src/drivers
	${fluidsynthdir}/include
)

#=====defines=====#
add_definitions(-DFLUIDSYNTH_NOT_A_DLL -DDEFAULT_SOUNDFONT="" -DHAVE_CONFIG_H=1)

#=====source=====#
if(DLAL_TEST)
	set(src ${src} "../src/test.cpp")
endif()

set(src ${src}
	${fluidsynthdir}/src/utils/fluid_conv.c
	${fluidsynthdir}/src/utils/fluid_hash.c
	${fluidsynthdir}/src/utils/fluid_list.c
	${fluidsynthdir}/src/utils/fluid_ringbuffer.c
	${fluidsynthdir}/src/utils/fluid_settings.c
	${fluidsynthdir}/src/utils/fluid_sys.c
	${fluidsynthdir}/src/sfloader/fluid_defsfont.c
	${fluidsynthdir}/src/sfloader/fluid_ramsfont.c
	${fluidsynthdir}/src/rvoice/fluid_adsr_env.c
	${fluidsynthdir}/src/rvoice/fluid_chorus.c
	${fluidsynthdir}/src/rvoice/fluid_iir_filter.c
	${fluidsynthdir}/src/rvoice/fluid_lfo.c
	${fluidsynthdir}/src/rvoice/fluid_rvoice.c
	${fluidsynthdir}/src/rvoice/fluid_rvoice_dsp.c
	${fluidsynthdir}/src/rvoice/fluid_rvoice_event.c
	${fluidsynthdir}/src/rvoice/fluid_rvoice_mixer.c
	${fluidsynthdir}/src/rvoice/fluid_rev.c
	${fluidsynthdir}/src/synth/fluid_chan.c
	${fluidsynthdir}/src/synth/fluid_event.c
	${fluidsynthdir}/src/synth/fluid_gen.c
	${fluidsynthdir}/src/synth/fluid_mod.c
	${fluidsynthdir}/src/synth/fluid_synth.c
	${fluidsynthdir}/src/synth/fluid_tuning.c
	${fluidsynthdir}/src/synth/fluid_voice.c
	${fluidsynthdir}/src/midi/fluid_midi.c
	${fluidsynthdir}/src/midi/fluid_midi_router.c
	${fluidsynthdir}/src/midi/fluid_seqbind.c
	${fluidsynthdir}/src/midi/fluid_seq.c
	${fluidsynthdir}/src/drivers/fluid_adriver.c
	${fluidsynthdir}/src/drivers/fluid_mdriver.c
	${fluidsynthdir}/src/drivers/fluid_aufile.c
	${fluidsynthdir}/src/bindings/fluid_cmd.c
	${fluidsynthdir}/src/bindings/fluid_filerenderer.c
)

#=====products=====#
footer()
