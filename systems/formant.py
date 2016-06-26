import dlal

#components
network=dlal.Component('network'); network.port(9130)
commander=dlal.Commander()
s_voice=dlal.Sonic(); s_voice.i(0, 0, 0.25); s_voice.s(0, 1); s_voice.midi(0x90, 40, 0x7f)
s_noise=dlal.Sonic();
s_noise.i(0, 0, 4.00); s_noise.i(0, 1, 4.00)
s_noise.i(1, 0, 4.00); s_noise.i(1, 1, 4.00)
s_noise.m(1, 0.01)
s_noise.midi(0x90, 41, 0x7f)
f_voice=dlal.Fir(); f_voice.resize(128)
f_noise=dlal.Fir(); f_noise.resize(128)
multiplier=dlal.Component('multiplier'); multiplier.offset(1); multiplier.set(0.5); multiplier.gate(-0.001);
buffer_voice=dlal.Buffer(); buffer_voice.clear_on_evaluate('y')
buffer_noise=dlal.Buffer(); buffer_noise.clear_on_evaluate('y')
#system
network.connect(commander)
s_voice.connect(buffer_voice); f_voice.connect(buffer_voice)
s_noise.connect(buffer_noise); f_noise.connect(buffer_noise)
multiplier.connect(buffer_voice); multiplier.connect(buffer_noise)
system=dlal.SimpleSystem(
	[network, commander, s_voice, s_noise, f_voice, f_noise, multiplier, buffer_voice, buffer_noise],
	[s_voice, s_noise],
	[buffer_voice, buffer_noise]
)
#phonetic interface
def phonetic(text):
	key, pressed=text.decode('utf-8').split()
	if int(pressed):
		f_voice.phonetic_voice(key)
		f_noise.phonetic_noise(key)
for p in dlal.Fir.phonetics:
	commander.register_command(p, phonetic)
commander.register_command('Space', phonetic)
#go
go, ports=system.standard_system_functionality()
