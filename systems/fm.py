import dlal

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
	audio.start()
	if port: midi.open(port)

def quit():
	audio.finish()
	system.demolish()
	import sys
	sys.exit()

print('available midi ports:\n', midi.ports())
print('use the go function to start audio processing')
print('use the quit function to quit')
