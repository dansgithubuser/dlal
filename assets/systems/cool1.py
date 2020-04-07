import dlal

import midi

import sys

def sys_arg(i, f=str, default=None):
    if len(sys.argv) > i:
        return f(sys.argv[i])
    return default

# init
audio = dlal.Audio()
liner = dlal.Liner()
sonic1 = dlal.Sonic()
sonic2 = dlal.Sonic()
lpf = dlal.Lpf()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)
gain = dlal.Gain()

# add
audio.add(liner)
audio.add(sonic1)
audio.add(sonic2)
audio.add(lpf)
audio.add(buf)
audio.add(tape)
audio.add(gain)

# commands
liner.load('assets/midis/cool1.mid', immediate=True)
liner.advance(sys_arg(1, float, 0))

sonic_json = {
    "0": {
        "a": "0.01", "d": "6e-6", "s": "0.25", "r": "1e-4", "m": "1",
        "i0": "0", "i1": "0.5", "i2": "0.5", "i3": "0.1", "o": "0.125",
    },
    "1": {
        "a": "0.01", "d": "6e-6", "s": "0.125", "r": "2e-4", "m": "2",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "3e-6", "d": "3e-5", "s": "0", "r": "1e-4", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "3": {
        "a": "0.01", "d": "0.01", "s": "1", "r": "0.01", "m": "0.01",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
}
sonic1.from_json(sonic_json)
sonic2.from_json(sonic_json)

gain.set(0)

# connect
liner.connect(sonic1)
liner.connect(sonic2)
sonic1.connect(buf)
sonic2.connect(buf)
lpf.connect(buf)
buf.connect(tape)
gain.connect(buf)
buf.connect(audio)

# setup
end = sys_arg(2, float)
if end:
    duration = end - sys_arg(1, float, 0)
    runs = int(duration * 44100 / 64)
    with open('cool1.raw', 'wb') as file:
        for i in range(runs):
            audio.run()
            if i % (1 << 8) == 0xff:
                tape.to_file_i16le(1 << 14, file)
else:
    dlal.typical_setup()
