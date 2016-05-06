#lpf

import dlal

fm=dlal.Fm()
lpf=dlal.Component('lpf')
system=dlal.SimpleSystem([fm, lpf], test=True)
go, ports=system.standard_system_functionality()
