#converter, sonic pitch slide

import dlal

lfo=dlal.Buffer()
converter=dlal.Component('converter')
sonic_controller=dlal.SonicController()
lfo.connect(converter)
converter.connect(sonic_controller)
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([lfo, converter, sonic_controller], outputs=[sonic_controller], test=True)
lfo.lfo(system.sample_rate)
lfo.midi(0x90, 0, 0x40)
sonic_controller.control_set('m', 0, 0, 127)
go, ports=system.standard_system_functionality()
