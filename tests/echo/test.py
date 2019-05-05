#buffer, multiplier

import dlal

sonic = dlal.Sonic()
multiplier = dlal.Component('multiplier')
buffer = dlal.Component('buffer')
multiplier.set(0.5, immediate=True)
buffer.periodic_resize(256, immediate=True)
sonic.connect(buffer, immediate=True)
multiplier.connect(buffer, immediate=True)
dlal.SimpleSystem.log_2_samples_per_evaluation = 6
system = dlal.SimpleSystem([sonic, multiplier, buffer], outputs=[buffer], test=True)
go, ports = system.standard_system_functionality()
