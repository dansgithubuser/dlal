#converter, fm pitch slide

import dlal

lfo=dlal.Buffer()
converter=dlal.Component('converter')
fm=dlal.Fm()
lfo.connect(converter)
converter.connect(fm)
system=dlal.SimpleSystem([lfo, converter, fm], outputs=[fm], test=True)
lfo.lfo(system.sample_rate)
lfo.midi(0x90, 0, 0x40)
fm.control_set('m', 0, 0, 127)
go, ports=system.standard_system_functionality()
