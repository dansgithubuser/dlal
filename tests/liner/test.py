#liner

import dlal

log2SamplesPerCallback=6

#create
system=dlal.System()
raw=dlal.Component('raw')
liner=dlal.Liner(16<<log2SamplesPerCallback, 16<<log2SamplesPerCallback)
sonic_controller=dlal.SonicController()
#command
raw.set(44100, log2SamplesPerCallback)
liner.line('z')
#add
system.add(raw, slot=1)
system.add(liner, sonic_controller)
#connect
liner.connect(sonic_controller)
sonic_controller.connect(raw)
#start
raw.start()
