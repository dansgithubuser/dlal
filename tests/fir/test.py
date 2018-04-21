#fir

import dlal

sonic_controller=dlal.SonicController(); sonic_controller.i(0, 0, 0.25); sonic_controller.s(0, 1)
fir=dlal.Formant(); fir.resize(128); fir.phonetic_voice('q')
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([sonic_controller, fir], test=True)
go, ports=system.standard_system_functionality()
