#commander - live add

import dlal

sample_rate=44100
log_2_samples_per_callback=6

#create
system=dlal.System()
commander=dlal.Commander()
raw=dlal.Component('raw')
fm=dlal.Fm(sample_rate)
midi=dlal.Component('midi')
#connect
fm.connect_input(midi)
fm.connect_output(raw)
#command
raw.set(sample_rate, log_2_samples_per_callback)
def commander_callback(text): commander._report(text)
commander.set_callback(commander_callback)
commander.queue_add(midi, 0)
commander.queue_add(fm, 0)
midi.midi(0x90, 0x3C, 0x40)
#add
commander.add(system)
raw.add(system)
#start
raw.start()
