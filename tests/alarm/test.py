#converter, sonic pitch slide

import dlal

lfo=dlal.Buffer()
converter=dlal.Component('converter')
sonic=dlal.Sonic()
lfo.connect(converter)
converter.connect(sonic)
system=dlal.SimpleSystem([lfo, converter, sonic], outputs=[sonic], test=True)
lfo.lfo(system.sample_rate)
lfo.midi(0x90, 0, 0x40)
sonic.control_set('m', 0, 0, 127)
go, ports=system.standard_system_functionality()
