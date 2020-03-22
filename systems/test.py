import dlal

audio = dlal.Audio()
midi = dlal.Midi()

audio.add(midi)
audio.command('start')
