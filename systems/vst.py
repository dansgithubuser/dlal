import dlal, os

#create
system=dlal.System()
qweboard=dlal.Qweboard()
midi=dlal.Component('midi')
fm=dlal.Fm()
vst=dlal.Component('vst')
audio=dlal.Component('audio')
#command
audio.set(44100, 6)
#add
system.add(audio, qweboard, midi, fm, vst)
#connect
qweboard.connect(midi)
midi.connect(fm)
midi.connect(vst)
fm.connect(audio)
vst.connect(audio)
#start
fm.show_controls()

#main
vst.load(os.environ['DLAL_VST_PLUGIN_PATH'])
go, ports=dlal.standard_system_functionality(audio, midi)
