#buffer, multiplier

import dlal

sonic=dlal.Sonic()
multiplier=dlal.Component('multiplier')
buffer=dlal.Component('buffer')
multiplier.set(0.5)
buffer.periodic_resize(256)
sonic.connect(buffer)
multiplier.connect(buffer)
system=dlal.SimpleSystem([sonic, multiplier, buffer], outputs=[buffer], test=True)
go, ports=system.standard_system_functionality()
