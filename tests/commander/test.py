#commander

import dlal

#create
system=dlal.System()
commander=dlal.Commander()
raw=dlal.Component('raw')
sonic=dlal.Sonic()
midi=dlal.Component('midi')
#command
raw.set(44100, 6)
commander.queue_add(midi, sonic)
commander.queue_connect(commander, midi, sonic, raw)
commander.queue(0, 0, 'midi', 0x90, 0x3C, 0x40)
#add
system.add(raw, slot=1)
system.add(commander)
#start
raw.start()
