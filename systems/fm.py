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
go, quit, ports=dlal.standard_system_functionality(system, audio, midi)
