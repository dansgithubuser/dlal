#buffer, multiplier

import dlal

sample_rate=44100
log_2_samples_per_callback=6

#create
system=dlal.System()
midi=dlal.Component('midi')
fm=dlal.Fm(sample_rate)
buffer=dlal.Component('buffer')
multiplier=dlal.Component('multiplier')
raw=dlal.Component('raw')
#connect
fm.connect_input(midi)
fm.connect_output(buffer)
multiplier.connect_output(buffer)
raw.connect_input(buffer)
#command
midi.midi(0x90, 0x3C, 0x40)
buffer.resize(4<<log_2_samples_per_callback)
multiplier.set(0.5)
raw.set(sample_rate, log_2_samples_per_callback)
#add
midi.add(system)
buffer.add(system)
fm.add(system)
multiplier.add(system)
raw.add(system)
#start
raw.start()
