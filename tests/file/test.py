#filei, fileo

import dlal

sample_rate=44100
log_2_samples_per_callback=6

#-----out-----#
#create
system=dlal.System()
raw=dlal.Component('raw')
midi=dlal.Component('midi')
fileo=dlal.Component('fileo')
#command
raw.set(sample_rate, log_2_samples_per_callback)
midi.midi(0x90, 0x3C, 0x40)
fileo.name('file.txt')
#add
system.add(raw, slot=1)
system.add(midi, fileo)
#connect
midi.connect(fileo)
#start
raw.start()
#finish
fileo.finish()
raw.finish()
del system

#-----in-----#
#create
system=dlal.System()
raw=dlal.Component('raw')
filei=dlal.Component('filei')
sonic_controller=dlal.SonicController()
#command
raw.set(sample_rate, log_2_samples_per_callback)
filei.name('file.txt')
#add
system.add(raw, slot=1)
system.add(filei, sonic_controller)
#connect
filei.connect(sonic_controller)
sonic_controller.connect(raw)
#start
raw.start()
