import dlal

#create
system=dlal.System()
raw=dlal.Component('raw')
midi=dlal.Component('midi')
fm=dlal.Fm()
lpf=dlal.Component('lpf')
#command
raw.set(44100, 6)
midi.midi(0x90, 0x3C, 0x40)
#add
system.add(raw, slot=1)
system.add(midi, fm, lpf)
#connect
midi.connect(fm)
fm.connect(raw)
lpf.connect(raw)
#start
raw.start()
