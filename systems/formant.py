import dlal

#components
network=dlal.Component('network'); network.port(9130)
commander=dlal.Commander()
fm_voice=dlal.Fm(); fm_voice.i(0, 0, 0.25); fm_voice.s(0, 1); fm_voice.midi(0x90, 40, 0x7f)
fm_noise=dlal.Fm();
fm_noise.i(0, 0, 4.00); fm_noise.i(0, 1, 4.00)
fm_noise.i(1, 0, 4.00); fm_noise.i(1, 1, 4.00)
fm_noise.m(1, 0.01)
fm_noise.midi(0x90, 41, 0x7f)
fir_voice=dlal.Fir(); fir_voice.resize(128)
fir_noise=dlal.Fir(); fir_noise.resize(128)
multiplier=dlal.Component('multiplier'); multiplier.offset(1); multiplier.set(0.5); multiplier.gate(-0.001);
buffer_voice=dlal.Buffer(); buffer_voice.clear_on_evaluate('y')
buffer_noise=dlal.Buffer(); buffer_noise.clear_on_evaluate('y')
#system
network.connect(commander)
fm_voice.connect(buffer_voice); fir_voice.connect(buffer_voice)
fm_noise.connect(buffer_noise); fir_noise.connect(buffer_noise)
multiplier.connect(buffer_voice); multiplier.connect(buffer_noise)
system=dlal.SimpleSystem(
	[network, commander, fm_voice, fm_noise, fir_voice, fir_noise, multiplier, buffer_voice, buffer_noise],
	[fm_voice, fm_noise],
	[buffer_voice, buffer_noise]
)
#phonetic interface
def phonetic(text):
	key, pressed=text.decode().split()
	if int(pressed):
		fir_voice.phonetic_voice(key)
		fir_noise.phonetic_noise(key)
for p in dlal.Fir.phonetics:
	commander.register_command(p, phonetic)
commander.register_command('Space', phonetic)
#go
go, ports=system.standard_system_functionality()
