#lpf

import dlal

sonic=dlal.Sonic()
lpf=dlal.Component('lpf')
system=dlal.SimpleSystem([sonic, lpf], test=True)
go, ports=system.standard_system_functionality()
