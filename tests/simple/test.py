import dlal

sample_rate=44100
log_2_samples_per_callback=6

#create
system=dlal.System()
fm=dlal.Fm(sample_rate)
raw=dlal.Component('raw')
midi=dlal.Component('midi')
#connect
fm.connect_input(midi)
fm.connect_output(raw)
#command
raw.set(sample_rate, log_2_samples_per_callback)
midi.midi(0x90, 0x3C, 0x40)
#add
midi.add(system)
raw.add(system)
fm.add(system)
#start
raw.start()
