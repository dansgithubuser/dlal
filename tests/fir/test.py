#fir

import dlal

sonic=dlal.Sonic(); sonic.i(0, 0, 0.25); sonic.s(0, 1)
fir=dlal.Fir(); fir.resize(128); fir.phonetic_voice('q')
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([sonic, fir], test=True)
go, ports=system.standard_system_functionality()
