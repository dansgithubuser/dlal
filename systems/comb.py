import dlal

delay = dlal.Buffer()
multiplier = dlal.Component('multiplier')

system = dlal.SimpleSystem([delay, multiplier], outputs=[delay])

system.audio.connect(delay)
multiplier.connect(delay)

delay.periodic_resize(dlal.round_up(system.sample_rate//100, system.samples_per_evaluation))
multiplier.set('0.85')

go, ports = system.standard_system_functionality()
