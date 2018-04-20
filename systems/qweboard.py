import atexit
import dlal

qweboard=dlal.Qweboard()
audio=dlal.Component('audio')

system=dlal.System()

system.add(qweboard)
system.add(audio)

audio.start()

atexit.register(lambda: audio.finish())
