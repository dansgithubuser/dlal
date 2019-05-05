# soundfont

import dlal

soundfont = dlal.Component('soundfont')
dlal.SimpleSystem.log_2_samples_per_evaluation = 6
system = dlal.SimpleSystem([soundfont], test=True)
go, ports = system.standard_system_functionality()
