import dlal

audio=dlal.Component('audio')
fm1=dlal.Component('fm')
fm2=dlal.Component('fm')
midi=dlal.Component('midi')
sfml=dlal.Component('sfml')
buf=dlal.Component('buffer')
mul=dlal.Component('multiplier')
audio.command('set 22050 6')
buf.command('resize 64')
mul.command('set 64.0')
print midi.command('ports')
midi.command('open KeyRig')
fm1.connect(audio)
fm2.connect(audio)
midi.connect(fm1)
sfml.connect(fm2)
audio.connect(buf)
buf.connect(audio)
mul.connect(buf)
sfml.add()
midi.add()
mul.add()
audio.add()
fm1.add()
fm2.add()
buf.add()
audio.command('start')

raw_input()
