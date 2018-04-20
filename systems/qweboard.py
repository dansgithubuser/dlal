import dlal

qweboard=dlal.Qweboard()
audio=dlal.Component('audio')

system=dlal.System()

system.add(qweboard)
system.add(audio)
