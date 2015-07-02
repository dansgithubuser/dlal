import dlal, atexit

#create
system=dlal.System()
network=dlal.Component('network')
midi=dlal.Component('midi')
fm=dlal.Fm()
audio=dlal.Component('audio')
#command
audio.set(44100, 6)
#add
system.add(audio, network, midi, fm)
#connect
network.connect(fm)
midi.connect(fm)
fm.connect(audio)
#start
fm.show_controls()

def go(port=9089):
	atexit.register(lambda: audio.finish())
	audio.start()
	if type(port)==str:
		midi.open(port)
	else:
		network.open(port)

print('available midi ports:\n', midi.ports())
print('use the go function to start audio processing')
