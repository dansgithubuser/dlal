import dlal

system=dlal.System()
audio=dlal.Component('audio')

def loop():
	for i in range(1000000): audio.set(44100, 6)
