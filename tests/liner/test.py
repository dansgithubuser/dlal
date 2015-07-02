#liner

import dlal

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Component('liner')
fm=dlal.Fm()
#command
log2SamplesPerCallback=6
raw.set(44100, log2SamplesPerCallback)
liner.midi(0, 0x90, 0x3C, 0x40)
liner.resize(16<<log2SamplesPerCallback)
#add
system.add(raw, liner, fm)
#connect
liner.connect(fm)
fm.connect(raw)
#start
raw.start()
