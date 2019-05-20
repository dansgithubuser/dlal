import dlal

buffer = dlal.Buffer()
lfo = dlal.Buffer()
multiplier = dlal.Component('multiplier')
lfo.connect(buffer, immediate=True)
multiplier.connect(buffer, immediate=True)
system = dlal.SimpleSystem([buffer, lfo, multiplier], outputs=[multiplier])
system.audio.connect(system.audio, immediate=True)
buffer.clear_on_evaluate('y', immediate=True)
lfo.lfo(system.sample_rate//30, immediate=True)
lfo.midi(0x90, 0, 0x40, immediate=True)
go, ports = system.standard_system_functionality()
