#filei, fileo

import dlal, os

sample_rate=44100
log_2_samples_per_callback=6

#-----out-----#
#create
system=dlal.System()
midi=dlal.Component('midi')
fileo=dlal.Component('fileo')
raw=dlal.Component('raw')
#connect
fileo.connect_input(midi)
#command
raw.set(sample_rate, log_2_samples_per_callback)
midi.midi(0x90, 0x3C, 0x40)
fileo.name('file.txt')
#add
midi.add(system)
fileo.add(system)
raw.add(system)
#start
raw.start()
#finish
del fileo

#-----in-----#
#create
system=dlal.System()
filei=dlal.Component('filei')
fm=dlal.Fm(sample_rate)
raw=dlal.Component('raw')
#connect
fm.connect_input(filei)
fm.connect_output(raw)
#command
raw.set(sample_rate, log_2_samples_per_callback)
filei.name('file.txt')
filei.resize(1<<log_2_samples_per_callback)
#add
filei.add(system)
raw.add(system)
fm.add(system)
#start
raw.start()
