import dlal, os, platform, sys

#create
system=dlal.System()
raw=dlal.Component('raw')
midi=dlal.Component('midi')
soundfont=dlal.Component('soundfont')
#command
raw.set(44100, 6)
midi.midi(0x90, 0x3C, 0x40)
#add
system.add(raw, slot=1)
system.add(midi, soundfont)
#connect
midi.connect(soundfont)
soundfont.connect(raw)
#start
raw.start()
