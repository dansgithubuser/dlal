#buffer repeat-sound and pitch-sound, multiply two signals

import dlal

pitcher=dlal.Buffer()
buffer=dlal.Buffer()
lfo=dlal.Buffer()
multiplier=dlal.Component('multiplier')
lfo.connect(buffer, immediate=True)
multiplier.connect(buffer, immediate=True)
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem(
	[pitcher, buffer, lfo, multiplier],
	midi_receivers=[],
	outputs=[pitcher, multiplier],
	test=True,
	test_duration=1000
)
pitcher.lfo(int(system.sample_rate/8.1757989156))
pitcher.pitch_sound('y', immediate=True)
pitcher.midi(0x90, 60, 0x40, immediate=True)
buffer.clear_on_evaluate('y', immediate=True)
lfo.lfo(system.sample_rate//30)
lfo.midi(0x90, 0, 0x40, immediate=True)
go, ports=system.standard_system_functionality()
