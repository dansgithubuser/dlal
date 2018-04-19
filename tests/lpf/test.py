#lpf

import dlal

sonic=dlal.Sonic()
lpf=dlal.Component('lpf')
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([sonic, lpf], test=True)
go, ports=system.standard_system_functionality()
