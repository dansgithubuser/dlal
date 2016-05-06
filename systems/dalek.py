import dlal

buffer=dlal.Buffer()
lfo=dlal.Buffer()
multiplier=dlal.Component('multiplier')
lfo.connect(buffer)
multiplier.connect(buffer)
system=dlal.SimpleSystem([buffer, lfo, multiplier], [multiplier])
system.audio.connect(system.audio)
buffer.clear_on_evaluate('y')
lfo.lfo(system.sample_rate//30)
lfo.midi(0x90, 0, 0x40)
go, ports=system.standard_system_functionality()
