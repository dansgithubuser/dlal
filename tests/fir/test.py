# fir

import dlal

sonic = dlal.Sonic()
sonic.i(0, 0, 0.25, immediate=True)
sonic.s(0, 1, immediate=True)

fir = dlal.Formant()
fir.resize(128, immediate=True)

dlal.SimpleSystem.log_2_samples_per_evaluation = 6
system = dlal.SimpleSystem([sonic, fir], test=True)
fir.phonetic_voice('q')
go, ports = system.standard_system_functionality()
