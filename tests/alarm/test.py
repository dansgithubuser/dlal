# converter, sonic pitch slide

import dlal

lfo = dlal.Buffer()
converter = dlal.Component('converter')
sonic = dlal.Sonic()
lfo.connect(converter, immediate=True)
converter.connect(sonic, immediate=True)
dlal.SimpleSystem.log_2_samples_per_evaluation = 6
system = dlal.SimpleSystem([lfo, converter, sonic], outputs=[sonic], test=True)
lfo.lfo(system.sample_rate)
lfo.midi(0x90, 0, 0x40, immediate=True)
sonic.control_set('m', 0, 0, 127, immediate=True)
go, ports = system.standard_system_functionality()
