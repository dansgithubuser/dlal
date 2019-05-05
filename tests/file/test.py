#filei, fileo

import dlal

sample_rate = 44100
log_2_samples_per_evaluation = 6

#-----out-----#
# create
system = dlal.System()
raw = dlal.Component('raw')
midi = dlal.Component('midi')
fileo = dlal.Component('fileo')
# command
raw.set(sample_rate, log_2_samples_per_evaluation, immediate=True)
midi.midi(0x90, 0x3C, 0x40, immediate=True)
fileo.file_name('file.txt', immediate=True)
# add
system.add(raw, slot=1, immediate=True)
system.add(midi, fileo, immediate=True)
# connect
midi.connect(fileo, immediate=True)
# start
raw.start(immediate=True)
# finish
fileo.finish(immediate=True)
raw.finish(immediate=True)
del system

#-----in-----#
# create
system = dlal.System()
raw = dlal.Component('raw')
filei = dlal.Component('filei')
sonic_controller = dlal.SonicController()
# command
raw.set(sample_rate, log_2_samples_per_evaluation, immediate=True)
filei.file_name('file.txt', immediate=True)
# add
system.add(raw, slot=1, immediate=True)
system.add(filei, sonic_controller, immediate=True)
# connect
filei.connect(sonic_controller, immediate=True)
sonic_controller.connect(raw, immediate=True)
# start
raw.start(immediate=True)
