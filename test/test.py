import dlal, atexit

system=dlal.System()

audio=dlal.Component('audio')
fm=dlal.Component('fm')
midi=dlal.Component('midi')
sfml=dlal.Component('sfml')
buf=dlal.Component('buffer')
mul=dlal.Component('multiplier')
switch=dlal.Component('switch')

audio.command('set 22050 6')
buf.command('resize 64')
mul.command('set 64.0')
print midi.command('ports')
try: midi.command('open KeyRig')
except RuntimeError as e: print e.message

midi.connect(switch)
sfml.connect(switch)
switch.connect(fm)
fm.connect(audio)
audio.connect(buf)
mul.connect(buf)
buf.connect(audio)

sfml.add(system)
midi.add(system)
mul.add(system)
audio.add(system)
fm.add(system)
buf.add(system)
switch.add(system)

audio.command('start')
atexit.register(lambda: audio.command('finish'))
