#liner

import dlal

log2SamplesPerCallback=6

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Liner(16<<log2SamplesPerCallback, 16<<log2SamplesPerCallback)
fm=dlal.Fm()
#command
raw.set(44100, log2SamplesPerCallback)
liner.line('z')
#add
system.add(raw, slot=1)
system.add(liner, fm)
#connect
liner.connect(fm)
fm.connect(raw)
#start
raw.start()
