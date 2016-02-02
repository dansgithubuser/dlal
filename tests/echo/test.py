#buffer, multiplier

import dlal

log_2_samples_per_callback=6

#create
system=dlal.System()
raw=dlal.Component('raw')
midi=dlal.Component('midi')
fm=dlal.Fm()
buffer=dlal.Component('buffer')
multiplier=dlal.Component('multiplier')
#command
raw.set(44100, log_2_samples_per_callback)
midi.midi(0x90, 0x3C, 0x40)
buffer.resize(4<<log_2_samples_per_callback)
multiplier.set(0.5)
#add
system.add(raw, midi, fm, multiplier, buffer)
#connect
midi.connect(fm)
fm.connect(buffer)
multiplier.connect(buffer)
buffer.connect(raw)
#start
raw.start()
#finish
system.demolish()
