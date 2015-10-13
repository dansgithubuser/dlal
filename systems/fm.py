import dlal, atexit

#create
system=dlal.System()
qweboard=dlal.Qweboard()
midi=dlal.Component('midi')
fm=dlal.Fm()
audio=dlal.Component('audio')
#command
audio.set(44100, 6)
#add
system.add(audio, qweboard, midi, fm)
#connect
qweboard.connect(midi)
midi.connect(fm)
fm.connect(audio)
#start
fm.show_controls()

#main
def go(port=None):
	atexit.register(lambda: audio.finish())
	audio.start()
	if port: midi.open(port)

print('available midi ports:\n', midi.ports())
print('use the go function to start audio processing')
