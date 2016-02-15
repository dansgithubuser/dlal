import dlal

#create
system=dlal.System()
qweboard=dlal.Qweboard()
midi=dlal.Component('midi')
soundfont=dlal.Component('soundfont')
lpf=dlal.Component('lpf')
audio=dlal.Component('audio')
#command
audio.set(44100, 6)
#add
system.add(audio, qweboard, midi, soundfont, lpf)
#connect
qweboard.connect(midi)
midi.connect(soundfont)
midi.connect(lpf)
soundfont.connect(audio)
lpf.connect(audio)
#start
import os
soundfont.load(os.path.join('..', '..', 'components', 'soundfont', 'deps', 'SGM-V2.01.sf2'))

#main
go, ports=dlal.standard_system_functionality(audio, midi)
