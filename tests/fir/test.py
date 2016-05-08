#fir

import dlal

fm=dlal.Fm(); fm.i(0, 0, 0.25); fm.s(0, 1)
fir=dlal.Fir(); fir.resize(128); fir.phonetic_voice('q')
system=dlal.SimpleSystem([fm, fir], test=True)
go, ports=system.standard_system_functionality()
