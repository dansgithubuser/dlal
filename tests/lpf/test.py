#lpf

import dlal

sonic_controller=dlal.SonicController()
lpf=dlal.Component('lpf')
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([sonic_controller, lpf], test=True)
go, ports=system.standard_system_functionality()
