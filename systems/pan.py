import dlal

import time

audio = dlal.Audio(driver=True)
sonic = dlal.Sonic()
pan = dlal.Pan()
buf = dlal.Buf()
tape = dlal.Tape()

dlal.connect(
    sonic,
    [buf, '<+', pan],
    [audio, tape],
)

sonic.from_json({
    "0": {
        "a": 1, "d": 1, "s": 1, "r": 1, "m": 1,
        "i0": 0, "i1": 1, "i2": 1, "i3": 1, "o": 1,
    },
    "1": {
        "a": 1, "d": 1, "s": 1, "r": 1, "m": 3,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 1, "d": 1, "s": 1, "r": 1, "m": 5,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 1, "d": 1, "s": 1, "r": 1, "m": 7,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})
sonic.midi([0x90, 45, 0x40])

def pan_around(flip):
    if flip:
        file_name = 'pan-l.i16le'
    else:
        file_name = 'pan-r.i16le'
    file = open(file_name, 'wb')
    for i in range(360):
        pan.set(i, 1, flip=flip)
        for _ in range(10):
            audio.run()
            tape.to_file_i16le(file)
    file.close()

pan_around(False)
pan_around(True)
dlal.sound.i16le_to_flac_stereo('pan-l.i16le', 'pan-r.i16le', 'pan.flac')
