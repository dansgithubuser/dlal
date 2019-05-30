import dlal

sonic = dlal.Sonic()
lpf = dlal.Lpf()
reverb = dlal.Reverb()
buffer = dlal.Buffer()
multiplier = dlal.Multiplier()
filea = dlal.Filea()

with dlal.ImmediateMode() as mode:
    sonic.connect(buffer)
    lpf.connect(buffer)
    reverb.connect(buffer)
    multiplier.connect(buffer)
    buffer.connect(filea)

    sonic.load('tom')
    lpf.set(0.95)
    reverb.set(0.1)
    buffer.periodic_resize(2560)
    multiplier.set(0.5)
    filea.write_on_midi()

system = dlal.SimpleSystem([sonic, lpf, reverb, buffer, multiplier, filea], [sonic, filea], [buffer])
go, ports = system.standard_system_functionality()

s = system.system
