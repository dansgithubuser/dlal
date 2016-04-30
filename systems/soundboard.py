import dlal

#create
system=dlal.System()
qweboard=dlal.Qweboard()
midi=dlal.Component('midi')
soundboard=dlal.Buffer()
audio=dlal.Component('audio')
#command
soundboard.periodic_resize(64)
audio.set(44100, 6)
#add
system.add(audio, qweboard, midi, soundboard)
#connect
qweboard.connect(midi)
midi.connect(soundboard)
soundboard.connect(audio)

#main
soundboard.load_sounds()
go, ports=dlal.standard_system_functionality(audio, midi)
