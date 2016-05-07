#buffer, multiplier

import dlal

fm=dlal.Fm()
multiplier=dlal.Component('multiplier')
buffer=dlal.Component('buffer')
multiplier.set(0.5)
buffer.periodic_resize(256)
fm.connect(buffer)
multiplier.connect(buffer)
system=dlal.SimpleSystem([fm, multiplier, buffer], outputs=[buffer], test=True)
go, ports=system.standard_system_functionality()
