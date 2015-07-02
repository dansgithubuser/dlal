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
def commander_callback(text): dlal.report(text)
commander.set_callback(commander_callback)
commander.queue_add(midi)
commander.queue_add(fm)
commander.queue_connect(commander, midi)
commander.queue_connect(midi, fm)
commander.queue_connect(fm, raw)
commander.queue(0, 0, 'midi', 0x90, 0x3C, 0x40)
#add
system.add(raw, commander)
#start
raw.start()
