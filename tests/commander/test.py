#commander

import dlal

#create
system=dlal.System()
commander=dlal.Commander()
raw=dlal.Component('raw')
fm=dlal.Fm()
midi=dlal.Component('midi')
#command
raw.set(44100, 6)
commander.queue_add(midi, fm)
commander.queue_connect(commander, midi, fm, raw)
commander.queue_command(0, 'midi', 0x90, 0x3C, 0x40)
#add
system.add(raw, commander)
#start
raw.start()
