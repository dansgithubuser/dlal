import dlal

midi=dlal.Component('midi')
print(midi.ports())

network=dlal.Component('network')
network.open(9089)

looper=dlal.Looper()

midi_track=dlal.MidiTrack(midi, dlal.Fm(), 64000*8, 32000)
midi_track.container.line('b . e .  j . . n  b j n b  g n x .')

audio_track=dlal.AudioTrack(looper.audio, 64000*8)

looper.add(midi_track)
looper.play(midi_track, True, 0)
looper.replay(midi_track, True, 0)

looper.add(audio_track)
looper.play(audio_track, True, 0)
looper.replay(audio_track, True, 0)
